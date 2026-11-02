"""Transparent, implicit-feedback item-to-item recommender with a popularity fallback.

Training only sees historical interactions before the evaluation cutoff.
"""
from __future__ import annotations

from collections import defaultdict
import numpy as np
import pandas as pd
from scipy import sparse

EVENT_WEIGHTS = {"view": 1.0, "addtocart": 3.0, "transaction": 5.0}


def build_model(events: pd.DataFrame, category_lookup: dict[int, int] | None = None,
                max_items: int = 8000, min_item_visitors: int = 5,
                max_user_items: int = 25, neighbors_per_item: int = 35) -> dict:
    """Build on training events only; save a compact precomputed neighbor index."""
    e = events.loc[events.event.isin(EVENT_WEIGHTS), ["visitorid", "itemid", "event", "timestamp"]].copy()
    e["w"] = e.event.map(EVENT_WEIGHTS).astype('float32')
    # Popularity is by *unique visitors*, not views; helps resist repeated bot traffic.
    item_visitors = e.groupby('itemid', observed=True).visitorid.nunique()
    eligible = item_visitors[item_visitors >= min_item_visitors].nlargest(max_items).index.to_numpy(dtype=np.int32)
    if len(eligible) == 0:
        raise ValueError('No sufficiently active items for recommendation training.')
    e = e[e.itemid.isin(eligible)]
    # Only each visitor's latest distinct items (bounded to avoid bot-like co-occurrences).
    e = e.sort_values('timestamp').drop_duplicates(['visitorid','itemid'], keep='last')
    e = e.groupby('visitorid',sort=False,group_keys=False).tail(max_user_items)
    users, user_index = np.unique(e.visitorid.to_numpy(dtype=np.int32),return_inverse=True)
    items = np.sort(eligible)
    item_idx = np.searchsorted(items, e.itemid.to_numpy(dtype=np.int32))
    weights = np.sqrt(e.w.to_numpy(dtype='float32'))
    matrix = sparse.csr_matrix((weights, (user_index, item_idx)), shape=(len(users),len(items)),dtype=np.float32)
    # Down-weight users who touch many different items.
    row_nnz = np.diff(matrix.indptr)
    row_penalty = 1 / np.sqrt(np.maximum(row_nnz,1))
    normalized = sparse.diags(row_penalty.astype('float32')) @ matrix
    raw_pairs = (normalized.T @ normalized).tocsr()
    norms = np.sqrt(np.asarray(normalized.power(2).sum(axis=0)).ravel())
    neighbors: dict[int, list[tuple[int,float]]] = {}
    for i, item_id in enumerate(items):
        lo, hi = raw_pairs.indptr[i], raw_pairs.indptr[i+1]
        cols = raw_pairs.indices[lo:hi]
        values = raw_pairs.data[lo:hi] / (norms[i] * np.maximum(norms[cols],1e-12))
        mask = (cols != i) & (values > 0)
        cols, values = cols[mask], values[mask]
        if len(values) > neighbors_per_item:
            keep = np.argpartition(values,-neighbors_per_item)[-neighbors_per_item:]
            cols,values=cols[keep],values[keep]
        order=np.argsort(-values)
        neighbors[int(item_id)] = [(int(items[c]),float(values[k])) for k,c in enumerate(cols[order])]
    popularity = item_visitors.sort_values(ascending=False)
    pop_items = [int(v) for v in popularity.index[:1000]]
    item_category = {int(k):int(v) for k,v in (category_lookup or {}).items() if pd.notna(v)}
    category_pop:dict[int,list[int]] = defaultdict(list)
    for item in pop_items:
        if item in item_category: category_pop[item_category[item]].append(item)
    return dict(version='1.0', items=items.tolist(), neighbors=neighbors,
                popularity=pop_items, item_category=item_category,
                category_pop=dict(category_pop),
                settings={'max_items': max_items,'min_item_visitors': min_item_visitors,
                          'max_user_items':max_user_items,'neighbors_per_item':neighbors_per_item,
                          'weights':EVENT_WEIGHTS})


def recommend(model:dict, history:list[int], n:int=5, mode:str='similarity')->list[dict]:
    """Rank unseen items; support similarity, category blend and popularity baseline."""
    history = [int(x) for x in history]
    seen = set(history)
    scores:dict[int,float] = defaultdict(float)
    reasons={}
    cats = model.get('item_category', {})
    preferred = [cats[i] for i in history if i in cats]
    pref_cats=set(preferred)
    neighbors=model['neighbors']
    if mode not in {'similarity','category','popularity'}:
        raise ValueError('Unsupported mode')
    if mode!='popularity':
        # Prevent runaway score inflation for extremely long browsing histories.
        for source in list(dict.fromkeys(history))[-15:]:
            for item, strength in neighbors.get(source, []):
                if item not in seen:
                    boost = 1.25 if mode=='category' and cats.get(item) in pref_cats else 1.0
                    scores[item]+=strength*boost
                    reasons[item]='Similar to products in browsing history'
    if mode=='category':
        for category in pref_cats:
            for rank,item in enumerate(model.get('category_pop',{}).get(category,[])[:80]):
                if item not in seen:
                    scores[item] += 0.035/(1+rank/15)
                    reasons.setdefault(item,'Popular in a category you browsed')
    # Global fallback makes the recommender usable even with no history.
    for rank,item in enumerate(model['popularity']):
        if item not in seen:
            scores[item] += (0.008/(1+rank/100)) if mode!='popularity' else (1/(1+rank))
            reasons.setdefault(item,'Popular across shoppers')
    ranked=sorted(scores, key=lambda x:(-scores[x],x))[:n]
    return [{'itemid':int(i),'score':round(float(scores[i]),5),
             'reason':reasons.get(i,'Popular across shoppers'),
             'categoryid':cats.get(i)} for i in ranked]


def evaluate_model(model:dict, history:dict[int,list[int]], truth:dict[int,set[int]],
                   k:int=5, mode:str='similarity', limit:int|None=None)->dict:
    """Warm-user offline next-period ranking metrics, with explicit denominator."""
    users=sorted(set(history)&set(truth))
    if limit is not None:users=users[:limit]
    if not users:return {'users':0,'precision_at_5':None,'recall_at_5':None,'hit_rate_at_5':None,'coverage':None}
    precisions=[]; recalls=[]; hits=[]; recommended=set(); num_catalog=len(model['items'])
    for u in users:
        recs=recommend(model,history[u],k,mode)
        ids={r['itemid'] for r in recs}
        relevant=truth[u]-set(history[u])
        if not relevant:continue
        n_hits=len(ids&relevant)
        precisions.append(n_hits/k)
        recalls.append(n_hits/len(relevant))
        hits.append(float(n_hits>0))
        recommended.update(ids)
    return {'users':len(precisions),
            'precision_at_5':round(float(np.mean(precisions)),6) if precisions else None,
            'recall_at_5':round(float(np.mean(recalls)),6) if recalls else None,
            'hit_rate_at_5':round(float(np.mean(hits)),6) if hits else None,
            'coverage':round(len(recommended)/num_catalog,6) if num_catalog else None}


def get_user_histories(events:pd.DataFrame, min_items:int=1,max_items:int=20)->dict[int,list[int]]:
    unique=events.sort_values('timestamp').drop_duplicates(['visitorid','itemid'],keep='last')
    vals=unique.groupby('visitorid',sort=False).itemid.agg(list)
    return {int(u):[int(i) for i in ids[-max_items:]] for u,ids in vals.items() if len(ids)>=min_items}

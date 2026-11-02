"""Reproducible full-data build: analytics, categories, recommendations, evaluation."""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.analytics import resolve_root, summarize_events, buyer_funnel, visitor_segment
from src.recommender import build_model,get_user_histories,evaluate_model,recommend


def dump(obj,p):
    p.parent.mkdir(parents=True,exist_ok=True)
    with open(p,'w',encoding='utf-8') as f:json.dump(obj,f,indent=2,allow_nan=False)

def read_properties(src:Path)->pd.DataFrame:
    rows=[]
    for name in ['item_properties_part1.csv','item_properties_part2.csv']:
        print('Reading category history:',name,flush=True)
        for chunk in pd.read_csv(src/name, chunksize=350_000,
                 usecols=['timestamp','itemid','property','value'],
                 dtype={'timestamp':'int64','itemid':'int32','property':'str','value':'str'}):
            c=chunk.loc[chunk.property.eq('categoryid'),['timestamp','itemid','value']].copy()
            if len(c): rows.append(c)
    prop=pd.concat(rows,ignore_index=True)
    prop['categoryid']=pd.to_numeric(prop.pop('value'),errors='coerce')
    prop=prop.dropna(subset=['categoryid'])
    prop['categoryid']=prop['categoryid'].astype('int32')
    prop=prop.sort_values('timestamp').drop_duplicates(['itemid','timestamp'],keep='last')
    print('Historical item category records:',len(prop),flush=True)
    return prop

def build(root:Path,source:Path,max_items:int=8000):
    out=root/'data'/'processed';out.mkdir(parents=True,exist_ok=True)
    tic=time.time()
    print('Loading raw interaction events...',flush=True)
    ev=pd.read_csv(source/'events.csv',dtype={'timestamp':'int64','visitorid':'int32','itemid':'int32','event':'category','transactionid':'float64'})
    ev=ev.loc[ev.event.isin(['view','addtocart','transaction'])].copy()
    ev=ev.dropna(subset=['timestamp','visitorid','itemid']).sort_values('timestamp').reset_index(drop=True)
    summary=summarize_events(ev)
    summary['funnel_visitors']=buyer_funnel(ev)
    # Exact analytics based only on events; product metadata is optional context.
    ev['date']=pd.to_datetime(ev.timestamp,unit='ms',utc=True).dt.strftime('%Y-%m-%d')
    daily=ev.groupby(['date','event'],observed=True).agg(
        events=('itemid','size'),visitor_days=('visitorid','nunique'),unique_products=('itemid','nunique')).reset_index()
    daily.to_csv(out/'daily_events.csv',index=False)
    # Per-date unique orders; transactions contain one row per purchased item.
    orders=ev.loc[ev.event=='transaction'].groupby('date').transactionid.nunique().reset_index(name='orders')
    orders.to_csv(out/'daily_orders.csv',index=False)
    # Segment at the visitor level, mutually exclusive using highest attained interaction stage.
    touch=ev.groupby(['visitorid','event'],observed=True).size().unstack(fill_value=0)
    for c in ('view','addtocart','transaction'):
        if c not in touch.columns:touch[c]=0
    segment=np.select([touch['transaction']>0,touch['addtocart']>0,touch['view']>0],
                       ['Purchaser','Cart engager','Browser'],default='Other')
    seg_counts=pd.Series(segment).value_counts()
    segments=[{'segment':str(k),'visitors':int(v)} for k,v in seg_counts.items()]
    dump(segments,out/'segments.json')
    # Avoid using pre-merged file: as-of join prevents future category look-ahead.
    cat=read_properties(source)
    tree=pd.read_csv(source/'category_tree.csv')
    parents={int(r.categoryid):int(r.parentid) for r in tree.itertuples() if pd.notna(r.parentid)}
    root_map={int(c):resolve_root(int(c),parents) for c in tree.categoryid}
    ev_with_category=pd.merge_asof(ev[['timestamp','itemid']].sort_values('timestamp'),
                cat.sort_values('timestamp'),on='timestamp',by='itemid',direction='backward')
    ev['categoryid']=ev_with_category['categoryid'].to_numpy()
    summary['events_with_asof_category']=int(ev.categoryid.notna().sum())
    summary['category_coverage_pct']=round(100*summary['events_with_asof_category']/len(ev),2)
    ev['root_category']=ev.categoryid.map(root_map).fillna(ev.categoryid)
    del ev_with_category
    # Product leaderboard and category aggregates: event counts, not inferred sales dollars.
    prods=ev.groupby(['itemid','event'],observed=True).size().unstack(fill_value=0)
    for c in ('view','addtocart','transaction'):
        if c not in prods.columns:prods[c]=0
    prods=prods.rename(columns={'view':'views','addtocart':'carts','transaction':'purchases'}).reset_index()
    # Most recent observed category per product, not intended for retrospective KPI joins.
    latest=cat.sort_values('timestamp').drop_duplicates('itemid',keep='last').set_index('itemid').categoryid
    prods['categoryid']=prods.itemid.map(latest)
    prods['root_category']=prods.categoryid.map(root_map).fillna(prods.categoryid)
    # Only the most relevant 10K products shipped for fast UI; aggregate category metrics uses all events.
    prods['interaction_total']=prods.views+prods.carts+prods.purchases
    prods.nlargest(10000,'interaction_total').sort_values('interaction_total',ascending=False).to_csv(out/'top_products.csv',index=False)
    known=ev.loc[ev.root_category.notna(),['root_category','event','visitorid','itemid']]
    grp=known.groupby(['root_category','event'],observed=True).agg(
               events=('itemid','size'),visitors=('visitorid','nunique'),products=('itemid','nunique')).reset_index()
    grp['root_category']=grp.root_category.astype(int)
    grp.to_csv(out/'category_events.csv',index=False)
    root_sizes=grp.groupby('root_category').events.sum().sort_values(ascending=False)
    dump([{'categoryid':int(k),'events':int(v)} for k,v in root_sizes.items()],out/'category_list.json')
    # Recs trained on chronological subset; no test-period interactions in models.
    q80=int(ev.timestamp.quantile(.8));q90=int(ev.timestamp.quantile(.9))
    train=ev.loc[ev.timestamp<=q80,['timestamp','visitorid','itemid','event']].copy()
    valid=ev.loc[(ev.timestamp>q80)&(ev.timestamp<=q90),['timestamp','visitorid','itemid','event']]
    test=ev.loc[ev.timestamp>q90,['timestamp','visitorid','itemid','event']]
    # Category features must also be restricted to the training cutoff (no future property snapshots).
    train_latest=cat.loc[cat.timestamp<=q80].sort_values('timestamp').drop_duplicates('itemid',keep='last').set_index('itemid').categoryid
    item_category={int(k):int(root_map.get(int(v),int(v))) for k,v in train_latest.items() if pd.notna(v)}
    print('Fitting recommendation engine on first 80% of timeline...',flush=True)
    model=build_model(train,item_category,max_items=max_items)
    # Only warm visitors with a history in training can be evaluated for personalization.
    train_hist=get_user_histories(train,max_items=20)
    def truth_map(future):
        # Events subsequent to training cutoff, valid items can include the full catalog.
        return {int(u):set(int(i) for i in ids) for u,ids in future.groupby('visitorid').itemid.unique().items() if int(u) in train_hist}
    val_truth=truth_map(valid);test_truth=truth_map(test)
    def measure(h,t):
        h={u:train_hist[u] for u in t}
        return {mode:evaluate_model(model,h,t,mode=mode) for mode in ('popularity','similarity','category')}
    metrics={'validation':measure(train_hist,val_truth),'test':measure(train_hist,test_truth),
             'protocol':'Global chronological event split 80/10/10; predictions use history at the 80% cutoff; unseen future interactions are relevant targets; warm users only.',
             'train_cutoff_utc':str(pd.to_datetime(q80,unit='ms',utc=True)),
             'validation_cutoff_utc':str(pd.to_datetime(q90,unit='ms',utc=True)),
             'train_events':len(train),'validation_events':len(valid),'test_events':len(test),
             'catalog_items':len(model['items']),'warm_validation_users':len(val_truth),'warm_test_users':len(test_truth),
             'cold_start_note':'People without training history are excluded from offline warm-user metrics and served via popularity fallback in the demo.',
             'limitation':'Metrics are offline proxy metrics on historical implicit feedback, not controlled uplift or revenue impact.'}
    print('Validation results:',metrics['validation'],flush=True)
    print('Test results:',metrics['test'],flush=True)
    dump(metrics,out/'model_metrics.json')
    # Keep the trained 80% model consistent with its published held-out test metrics.
    joblib.dump(model,out/'recommender.joblib',compress=3)
    # Select good demo visitors from TRAIN period; store their history only. Prioritize 2+ items.
    sample=[(u,ids) for u,ids in train_hist.items() if 2<=len(ids)<=20 and any(i in model['neighbors'] for i in ids)]
    sample.sort(key=lambda x:(-len(x[1]),x[0]))
    sample=sample[:200]
    demo=[{'visitorid':int(u),'interactions':len(ids),'history':ids,
           'top_recs':[r['itemid'] for r in recommend(model,ids,5)]} for u,ids in sample]
    dump(demo,out/'demo_visitors.json')
    summary['analyzed_in_utc']=True
    summary['model_train_events']=len(train)
    summary['model_catalog_items']=len(model['items'])
    summary['source']='Retailrocket historical 2015 events; uploaded raw CSV files'
    summary['notes']='Events are not revenue; visitor funnel stages are reach, not ordered user journeys.'
    dump(summary,out/'summary.json')
    print('Finished in',round(time.time()-tic,1),'seconds',flush=True)
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,required=True)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--max-items',type=int,default=8000)
    args=parser.parse_args()
    build(args.root,args.input_dir,args.max_items)

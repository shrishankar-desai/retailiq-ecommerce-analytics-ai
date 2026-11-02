"""Generate fictional retail activity, independent of Retailrocket source data.

Writes four CSVs compatible with scripts/build.py. This is an illustrative
portfolio dataset, NOT evidence of a real business, customers, or sales.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def generate(out: Path, visitors: int=1800, items: int=240, seed: int=2026) -> None:
    if visitors < 50 or items < 30:
        raise ValueError('Use at least 50 visitors and 30 items')
    out.mkdir(parents=True, exist_ok=True)
    rng=np.random.default_rng(seed)
    start=int(pd.Timestamp('2025-01-01',tz='UTC').timestamp()*1000)
    end_days=90
    categories=max(3,items//35)
    item_ids=np.arange(10001,10001+items,dtype=np.int32)
    cat_for_item=np.array([100+(i % categories) for i in range(items)],dtype=np.int32)
    # Small intentional hierarchy (category -> root).
    tree=pd.DataFrame([{'categoryid':10,'parentid':np.nan}] +
        [{'categoryid':int(c),'parentid':10} for c in np.unique(cat_for_item)])
    tree.to_csv(out/'category_tree.csv',index=False)
    prop=[{'timestamp':start-86400000,'itemid':int(item),'property':'categoryid','value':str(int(cat))}
          for item,cat in zip(item_ids,cat_for_item)]
    pd.DataFrame(prop).to_csv(out/'item_properties_part1.csv',index=False)
    # Second file is genuinely distinct from part1 and exercises 2-part loader.
    pd.DataFrame([{'timestamp':start+24*86400000,'itemid':int(item_ids[i]),
        'property':'categoryid','value':str(int(cat_for_item[i]))}
        for i in range(0,items,7)]).to_csv(out/'item_properties_part2.csv',index=False)
    events=[]
    transaction=400001
    # Visitors have preferences and return across time: creates a realistic
    # train/test distinction without borrowing any real dataset values.
    for user in range(visitors):
        favorite=int(rng.integers(0,categories))
        sessions=int(rng.integers(4,12))
        days=np.sort(rng.choice(end_days,size=sessions,replace=True))
        for d in days:
            visits=int(rng.integers(2,7))
            t=int(start+int(d)*86400000+rng.integers(0,86400000-200000))
            for step in range(visits):
                cat=favorite if rng.random()<0.82 else int(rng.integers(0,categories))
                candidates=item_ids[cat_for_item==100+cat]
                # Bias toward more frequent products within category.
                weights=1/np.sqrt(np.arange(1,len(candidates)+1))
                item=int(rng.choice(candidates,p=weights/weights.sum()))
                events.append((t+step*30000,user+100000,item,'view',np.nan))
                if rng.random()<0.12:
                    events.append((t+step*30000+1500,user+100000,item,'addtocart',np.nan))
                    if rng.random()<0.35:
                        transaction+=1
                        events.append((t+step*30000+3000,user+100000,item,'transaction',float(transaction)))
    df=pd.DataFrame(events,columns=['timestamp','visitorid','itemid','event','transactionid'])
    df.to_csv(out/'events.csv',index=False)
    print(f'Generated {len(df):,} synthetic events; {visitors} visitors; {items} products; files: {out}')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=Path('synthetic_demo/input_data'))
    parser.add_argument('--visitors',type=int,default=1800)
    parser.add_argument('--items',type=int,default=240)
    parser.add_argument('--seed',type=int,default=2026)
    a=parser.parse_args();generate(a.output_dir,a.visitors,a.items,a.seed)

import pandas as pd
from src.recommender import build_model, recommend, evaluate_model

def toy():
    rows=[]
    histories={1:[10,11],2:[10,12],3:[10,11,12],4:[10,12],5:[10,11]}
    for u,items in histories.items():
        for j,item in enumerate(items):rows.append({'visitorid':u,'itemid':item,'event':'view','timestamp':1000+u*10+j})
    return pd.DataFrame(rows)

def test_recommender_excludes_seen_and_fallback():
    m=build_model(toy(),min_item_visitors=1,max_items=10)
    r=recommend(m,[10],5)
    assert r and all(v['itemid']!=10 for v in r)
    assert recommend(m,[],2,mode='popularity')
    metrics=evaluate_model(m,{1:[10]},{1:{11}},mode='similarity')
    assert metrics['users']==1
    assert 0<=metrics['precision_at_5']<=1

def test_mode_validation():
    m=build_model(toy(),min_item_visitors=1,max_items=10)
    try: recommend(m,[10],5,mode='unknown')
    except ValueError: pass
    else: assert False

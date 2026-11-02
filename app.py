"""Retail Intelligence Studio — API and offline-ready client dashboard.

Run: python -m uvicorn app:app --reload
"""
from __future__ import annotations
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.recommender import recommend

BASE=Path(__file__).resolve().parent
DATA=Path(os.environ.get('RETAILIQ_DATA_DIR', str(BASE/'data'/'processed'))).resolve()
app=FastAPI(title='Retail Intelligence Studio',version='1.0.0',description='Synthetic e-commerce analytics and offline item recommendations')
app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')

@lru_cache(maxsize=24)
def load_json(name:str):
    with open(DATA/name,encoding='utf-8') as f:return json.load(f)

@lru_cache(maxsize=24)
def load_csv(name:str)->pd.DataFrame:
    return pd.read_csv(DATA/name)

@lru_cache(maxsize=1)
def model():
    return joblib.load(DATA/'recommender.joblib')

@app.get('/',include_in_schema=False)
def index():return FileResponse(BASE/'static'/'index.html')

@app.get('/api/health')
def health():
    return {'status':'ok','data_ready':(DATA/'summary.json').exists(),
            'recommender_ready':(DATA/'recommender.joblib').exists()}

@app.get('/api/summary')
def summary():return load_json('summary.json')

@app.get('/api/trends')
def trends(start:str|None=None,end:str|None=None):
    df=load_csv('daily_events.csv')
    if start:df=df[df.date>=start]
    if end:df=df[df.date<=end]
    # Return additive counts and summed daily visitors (visitor-days) only.
    out=df.pivot_table(index='date',columns='event',values='events',aggfunc='sum',fill_value=0).reset_index()
    for c in ['view','addtocart','transaction']:
        if c not in out:out[c]=0
    visits=df.groupby('date').visitor_days.max() # max daily event reach is not a true union; don't present as unique.
    result=out[['date','view','addtocart','transaction']].copy()
    order_df=load_csv('daily_orders.csv')
    result=result.merge(order_df,on='date',how='left').fillna({'orders':0})
    return {'data':result.to_dict(orient='records'),
            'totals':{'views':int(result['view'].sum()),'carts':int(result.addtocart.sum()),
                      'purchases':int(result.transaction.sum()), 'orders':int(result.orders.sum()),
                      'event_count':int(result[['view','addtocart','transaction']].sum().sum())}}

@app.get('/api/products')
def products(category:int|None=None,sort:Literal['views','carts','purchases','interaction_total']='views',
             search:str|None=None,limit:int=Query(30,ge=1,le=500)):
    df=load_csv('top_products.csv')
    if category is not None:df=df[df.root_category==category]
    if search:
        df=df[df.itemid.astype(str).str.contains(search,regex=False)]
    df=df.sort_values(sort,ascending=False).head(limit)
    df=df.where(pd.notna(df),None)
    return {'products':json.loads(df.to_json(orient='records')),'shown':len(df),
            'note':'Leaderboard covers the 10,000 most-interacted-with items, not every item in the dataset.'}

@app.get('/api/categories')
def categories():return load_json('category_list.json')

@app.get('/api/category-stats')
def category_stats():
    df=load_csv('category_events.csv')
    table=df.pivot_table(index='root_category',columns='event',values='events',aggfunc='sum',fill_value=0).reset_index()
    for c in ('view','addtocart','transaction'):
        if c not in table:table[c]=0
    return table.sort_values('view',ascending=False).to_dict(orient='records')

@app.get('/api/segments')
def segments():return load_json('segments.json')

@app.get('/api/visitors')
def visitors():
    return [{'visitorid':v['visitorid'],'interactions':v['interactions']} for v in load_json('demo_visitors.json')]

@app.get('/api/recommend')
def get_recommendations(visitorid:int,mode:Literal['similarity','category','popularity']='similarity'):
    matches=[v for v in load_json('demo_visitors.json') if v['visitorid']==visitorid]
    if not matches:raise HTTPException(404,'Visitor is not in the curated anonymous demo sample')
    row=matches[0]
    recs=recommend(model(),row['history'],n=5,mode=mode)
    return {'visitorid':visitorid,'history':row['history'],'mode':mode,'recommendations':recs,
            'note':'Offline demo with entirely synthetic visitor/item interactions; not live customer behavior.'}

@app.get('/api/model')
def performance():return load_json('model_metrics.json')

@app.get('/api/download/products')
def download_products():
    return FileResponse(DATA/'top_products.csv',filename='rocket_top_products.csv',media_type='text/csv')

@app.get('/api/download/daily')
def download_daily():
    return FileResponse(DATA/'daily_events.csv',filename='rocket_daily_events.csv',media_type='text/csv')

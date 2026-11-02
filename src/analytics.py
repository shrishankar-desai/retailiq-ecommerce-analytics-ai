"""Pure analytics functions shared by the preparation workflow and tests."""
from __future__ import annotations
import pandas as pd
import numpy as np

def visitor_segment(views:int,carts:int,purchases:int)->str:
    if purchases>0:return 'Purchaser'
    if carts>0:return 'Cart engager'
    if views>0:return 'Browser'
    return 'Other'

def resolve_root(category:int, parents:dict[int,int])->int:
    seen=set()
    node=int(category)
    while node in parents and parents[node] != node and node not in seen:
        seen.add(node)
        node=int(parents[node])
    return node

def summarize_events(events:pd.DataFrame)->dict:
    counts=events.event.value_counts().to_dict()
    return {
        'events':int(len(events)),
        'visitors':int(events.visitorid.nunique()),
        'products':int(events.itemid.nunique()),
        'views':int(counts.get('view',0)),
        'addtocarts':int(counts.get('addtocart',0)),
        'transaction_events':int(counts.get('transaction',0)),
        'orders':int(events.transactionid.nunique()),
        'first_date':str(pd.to_datetime(events.timestamp.min(),unit='ms',utc=True).date()),
        'last_date':str(pd.to_datetime(events.timestamp.max(),unit='ms',utc=True).date()),
    }

def buyer_funnel(events:pd.DataFrame)->dict:
    """Unique visitor reach for each event type, not a sequential conversion rate."""
    reach=events.groupby('event',observed=True).visitorid.nunique().to_dict()
    return {k:int(reach.get(k,0)) for k in ['view','addtocart','transaction']}

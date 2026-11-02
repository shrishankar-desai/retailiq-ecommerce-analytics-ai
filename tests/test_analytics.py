import pandas as pd
from src.analytics import summarize_events, visitor_segment, resolve_root, buyer_funnel

def test_summary_orders_are_not_purchase_events():
    ev=pd.DataFrame({'timestamp':[1433221332117]*3,'visitorid':[1,1,2],
       'itemid':[7,8,9],'event':['transaction','transaction','view'],
       'transactionid':[77.,77.,float('nan')]})
    s=summarize_events(ev)
    assert s['events']==3 and s['orders']==1 and s['transaction_events']==2
    assert buyer_funnel(ev)['transaction']==1

def test_segment_and_tree():
    assert visitor_segment(9,0,0)=='Browser'
    assert visitor_segment(2,1,0)=='Cart engager'
    assert visitor_segment(1,1,1)=='Purchaser'
    assert resolve_root(4,{4:3,3:2})==2

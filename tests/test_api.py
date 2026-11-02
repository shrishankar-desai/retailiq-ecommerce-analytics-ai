from fastapi.testclient import TestClient
from app import app

client=TestClient(app)

def test_health_and_summary():
    assert client.get('/api/health').json()['status']=='ok'
    summary=client.get('/api/summary').json()
    assert summary['events']==2756101
    assert summary['visitors']==1407580
    assert summary['orders']<=summary['transaction_events']

def test_products_and_trends():
    r=client.get('/api/products?sort=purchases&limit=10')
    assert r.status_code==200
    products=r.json()['products']
    assert len(products)==10
    assert all(products[i]['purchases']>=products[i+1]['purchases'] for i in range(9))
    assert len(client.get('/api/trends').json()['data'])>100


def test_user_recommendations_exclude_history():
    v=client.get('/api/visitors').json()[0]['visitorid']
    r=client.get(f'/api/recommend?visitorid={v}&mode=similarity').json()
    assert len(r['recommendations'])==5
    assert not (set(r['history'])&{i['itemid'] for i in r['recommendations']})
    assert client.get('/api/recommend?visitorid=-1').status_code==404
    assert client.get('/api/recommend?visitorid=1&mode=invalid').status_code==422


def test_model_metrics():
    m=client.get('/api/model').json()
    assert m['train_events']+m['validation_events']+m['test_events']==2756101
    assert m['test']['category']['hit_rate_at_5']>m['test']['popularity']['hit_rate_at_5']

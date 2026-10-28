from fastapi.testclient import TestClient
from motorlab.api import app

client=TestClient(app)


def test_health_has_no_production_access():
    assert client.get('/api/v1/health').json()['production_access'] is False


def test_input_bounds_and_no_production_source():
    assert client.post('/api/v1/runs',json={'seed':-1}).status_code==422
    assert client.post('/api/v1/runs',json={'source':'influx'}).status_code==422
    assert client.post('/api/v1/runs',json={'window_seconds':100}).status_code==422
    assert client.get('/api/v1/runs?limit=10000').status_code==422


def test_no_cross_origin_writes():
    assert client.post('/api/v1/runs',json={},headers={'origin':'https://evil.example'}).status_code==403


def test_not_found_is_explicit():
    response=client.get('/api/v1/runs/missing/export')
    assert response.status_code==404 and 'error' in response.json()


def test_latest_and_waveform_consistency():
    response=client.get('/api/v1/runs/latest')
    assert response.status_code==200
    report=response.json(); rid=report['run_id']
    assert report['provenance']=='SIMULATED' and len(report['motors'])==3
    raw=client.get(f'/api/v1/runs/{rid}/waveform?motor_id=SIM-01&index=0').json()
    assert raw['waveform']==report['motors'][0]['waveform']
    assert client.get(f'/api/v1/runs/{rid}/features?motor_id=SIM-01&start=10&end=0').status_code==422
    assert client.get(f'/api/v1/runs/{rid}/features?motor_id=SIM-01&limit=3').json()['items'].__len__()==3
    assert client.get(f'/api/v1/runs/{rid}/export').json()['manifest']==report['manifest']


def test_notes_are_persistent(tmp_path,monkeypatch):
    import motorlab.api as api
    monkeypatch.setattr(api,'DATA',tmp_path)
    rid=client.get('/api/v1/runs/latest').json()['run_id']
    text="Engineer review: cause unknown; ' is literal"
    response=client.post(f'/api/v1/runs/{rid}/notes',json={'motor_id':'SIM-01','index':180,'text':text})
    assert response.status_code==201
    assert client.get(f'/api/v1/runs/{rid}/notes').json()['items'][-1]['text']==text

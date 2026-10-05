import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from backend.api import make_app
from backend.import_seed import import_seed
from backend.storage import Repository


def payload(start='10:00', end='11:00', ship=1, offset='-05:00', day='2026-07-14'):
    return {'shipId': ship, 'pilotName': 'Demo Pilot',
            'startTime': f'{day}T{start}:00{offset}', 'endTime': f'{day}T{end}:00{offset}'}


@pytest.fixture
def client(tmp_path):
    path = tmp_path / 'test.db'
    with TestClient(make_app(path)) as client:
        with Repository(str(path)).connection(writing=True) as db:
            db.executemany('INSERT INTO ship VALUES(?,?)', [(1, 'Serenity'), (2, 'Nostromo')])
        yield client


@pytest.mark.parametrize('start,end,expected', [
    ('09:00','09:30',201), ('09:30','10:00',409), ('10:00','10:30',409),
    ('10:30','11:00',409), ('11:00','11:30',409), ('11:30','12:00',201),
    ('09:29','09:31',409), ('09:00','12:00',409),
])
def test_turnaround_in_both_directions(client, start, end, expected):
    assert client.post('/api/bookings', json=payload()).status_code == 201
    assert client.post('/api/bookings', json=payload(start, end)).status_code == expected


@pytest.mark.parametrize('start,end,expected', [
    ('06:00','06:30',201), ('21:30','22:00',201), ('05:59','06:30',422),
    ('21:30','22:01',422), ('10:00','10:00',422), ('11:00','10:00',422),
])
def test_operating_hours(client, start, end, expected):
    assert client.post('/api/bookings', json=payload(start, end)).status_code == expected


def test_availability_and_ship_independence(client):
    client.post('/api/bookings', json=payload())
    assert client.post('/api/bookings', json=payload(ship=2)).status_code == 201
    data = client.get('/api/availability', params={'shipId':1,'day':'2026-07-14','duration':30}).json()
    slots = {slot['label']: slot['available'] for slot in data['slots']}
    assert slots['9:00 AM'] and slots['11:30 AM']
    assert not slots['9:30 AM'] and not slots['11:00 AM']
    assert 'pilotName' not in json.dumps(data)
    assert data['unavailable'] == [{'startTime':'2026-07-14T09:30:00-05:00','endTime':'2026-07-14T11:30:00-05:00'}]


@pytest.mark.parametrize('day,offset,utc', [('2026-01-14','-06:00','16:00'), ('2026-07-14','-05:00','15:00'), ('2026-03-08','-05:00','15:00'), ('2026-11-01','-06:00','16:00')])
def test_central_dst_and_storage(client, day, offset, utc):
    response = client.post('/api/bookings', json=payload(day=day, offset=offset))
    assert response.status_code == 201
    assert utc in response.json()['startTime']
    assert len(client.get('/api/bookings', params={'day':day}).json()) == 1


def test_invalid_inputs(client):
    assert client.post('/api/bookings', json=payload(ship=99)).status_code == 404
    item = payload(); item['pilotName'] = '   '
    assert client.post('/api/bookings', json=item).status_code == 422
    item = payload(); item['startTime'] = '2026-07-14T10:00:00'
    assert client.post('/api/bookings', json=item).status_code == 422
    item = payload(); item['endTime'] = '2026-07-15T11:00:00-05:00'
    assert client.post('/api/bookings', json=item).status_code == 422
    assert client.get('/api/availability', params={'shipId':1,'day':'2026-07-14','duration':45}).status_code == 422
    assert client.get('/api/availability', params={'shipId':99,'day':'2026-07-14'}).status_code == 404


def test_concurrent_attempts(client):
    barrier = Barrier(8)
    def submit(_):
        barrier.wait()
        return client.post('/api/bookings', json=payload()).status_code
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(submit, range(8)))
    assert sorted(results) == [201] + [409] * 7
    assert len(client.get('/api/bookings').json()) == 1


def test_import_rollback_and_repeat(tmp_path):
    source = tmp_path / 'seed.json'; database = tmp_path / 'seed.db'
    data = {'ships':[{'id':1,'name':'Serenity'}], 'bookings':[payload(),payload()]}
    source.write_text(json.dumps(data))
    with pytest.raises(Exception): import_seed(source, database)
    assert Repository(str(database)).ships() == []
    data['bookings'].pop(); source.write_text(json.dumps(data))
    assert import_seed(source, database) == (1,1)
    with pytest.raises(ValueError, match='not empty'): import_seed(source, database)
    assert len(Repository(str(database)).bookings()) == 1


def test_persistence(tmp_path):
    path = tmp_path / 'persist.db'
    with TestClient(make_app(path)) as client:
        with Repository(str(path)).connection(writing=True) as db:
            db.execute('INSERT INTO ship VALUES(1, "Serenity")')
        assert client.post('/api/bookings', json=payload()).status_code == 201
    with TestClient(make_app(path)) as client:
        assert len(client.get('/api/bookings').json()) == 1

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.services.exposure import rotate, issue, acknowledge, counts, database, ExposureStorageError, PostgresConnection
from app.data_loader import load_places
from app.services.route import next_places


class ExposureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'EXPOSURE_DB_PATH':str(Path(self.temp.name)/'exposure.sqlite3'),
                                         'EXPOSURE_DATABASE_URL':'', 'RENDER':''})
        self.env.start()
        self.places = [{'id':i,'leg_minutes':s/60,'leg_seconds':s} for i,s in
                       [('a',300),('b',360),('c',420),('far',421)]]

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_ack_once_rotation_and_distance_boundary(self):
        first = rotate(self.places)
        self.assertEqual([p['id'] for p in first],['a','b','c'])
        token = issue(first)
        self.assertEqual(counts(), {})  # API generation is not an impression.
        self.assertTrue(acknowledge(token))
        self.assertFalse(acknowledge(token))
        self.assertEqual(counts(), {'a':(1,1),'b':(0,1),'c':(0,1)})
        self.assertEqual([p['id'] for p in rotate(self.places)],['b','c','a'])
        # A fresh database connection retains the acknowledged list.
        self.assertEqual(counts()['a'],(1,1))

    def test_endpoint_validation_and_expired_history(self):
        client = TestClient(app)
        self.assertEqual(client.post('/api/recommend/impressions',json={'recommendation_id':'fake'}).status_code,422)
        self.assertEqual(client.post('/api/recommend/impressions',json={'recommendation_id':'00000000-0000-0000-0000-000000000000'}).status_code,404)
        token=issue(self.places[:1])
        with patch('app.services.exposure.time.time',return_value=10**12):
            with self.assertRaises(ValueError): acknowledge(token)
        acknowledge(token)
        with patch('app.services.exposure.time.time',return_value=10**12):
            self.assertEqual(counts(),{})

    def test_cloud_requires_database_and_history_is_retained(self):
        with patch.dict(os.environ, {'RENDER':'true'}):
            with self.assertRaises(ExposureStorageError): counts()
        token=issue(self.places[:1]); acknowledge(token)
        with patch('app.services.exposure.time.time',return_value=10**12):
            issue(self.places[:1])
        with database() as db:
            self.assertIsNotNone(db.execute('SELECT shown FROM lists WHERE id=?',(token,)).fetchone())

    def test_postgres_statements_parameterize_values(self):
        from unittest.mock import Mock
        connection=Mock()
        PostgresConnection(connection).execute('INSERT INTO lists(id,created,places) VALUES (?,?,?)',('id',1,'[]'))
        connection.execute.assert_called_once_with('INSERT INTO app_private.exposure_lists(id,created,places) VALUES (%s,%s,%s)',('id',1,'[]'))

    def test_database_errors_do_not_expose_credentials(self):
        import psycopg
        with patch.dict(os.environ, {'EXPOSURE_DATABASE_URL':'postgresql://private-secret'}), \
                patch('psycopg.connect',side_effect=psycopg.OperationalError('private-secret')):
            with self.assertRaises(ExposureStorageError) as error: counts()
            self.assertNotIn('private-secret',str(error.exception))

    @patch('app.services.route.walking_leg')
    def test_next_route_rotates_without_mutating_fixed_stops(self, walk):
        # All three tourist places remain feasible; fixed prefix is excluded.
        base={**load_places().iloc[0].to_dict(),'category':'관광명소','duration_min':30}
        import pandas as pd
        catalog=pd.DataFrame([{**base,'id':i,'lat':35.101+k*.001} for k,i in enumerate(['a','b','c','d'])])
        walk.return_value={'leg_minutes':5,'leg_seconds':300,'leg_path':[],'leg_distance_m':300}
        fixed=[catalog.iloc[0].to_dict()]
        first=next_places(catalog,35.1,129.03,fixed,'관광명소',180)
        acknowledge(issue(first['alternatives']))
        second=next_places(catalog,35.1,129.03,fixed,'관광명소',180)
        self.assertEqual([p['id'] for p in second['stops']],['a'])
        self.assertNotEqual(first['alternatives'][0]['id'],second['alternatives'][0]['id'])
        self.assertTrue(all(p['projected_total_minutes']<=180 and p['leg_seconds']<=1200 for p in second['alternatives']))

    @patch('app.services.route.walking_leg')
    def test_api_issues_list_then_acknowledges_once(self, walk):
        import pandas as pd
        base={**load_places().iloc[0].to_dict(),'category':'관광명소','duration_min':30}
        catalog=pd.DataFrame([{**base,'id':i,'lat':35.101+k*.001} for k,i in enumerate(['a','b','c'])])
        walk.return_value={'leg_minutes':5,'leg_seconds':300,'leg_path':[],'leg_distance_m':300}
        client=TestClient(app)
        body={'start_lat':35.1,'start_lon':129.03,'category':'관광명소','max_minutes':180}
        with patch('app.routers.recommend.load_places',return_value=catalog):
            response=client.post('/api/recommend/next',json=body)
            self.assertEqual(response.status_code,200)
            first=response.json()
            self.assertEqual(counts(),{})
            payload={'recommendation_id':first['recommendation_id']}
            self.assertTrue(client.post('/api/recommend/impressions',json=payload).json()['recorded'])
            self.assertFalse(client.post('/api/recommend/impressions',json=payload).json()['recorded'])
            second=client.post('/api/recommend/next',json=body).json()
            self.assertNotEqual(first['alternatives'][0]['id'],second['alternatives'][0]['id'])


if __name__=='__main__': unittest.main()

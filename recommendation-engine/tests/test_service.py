from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from service.app import create_app
from genai.enrichment import sha


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine=Mock()
        self.engine.signals.return_value=({},0,[])
        self.engine.predict.return_value=([7],'global_popularity')
        self.config={'cutoff_ms':100,'status':'validation_selected_not_final_test_freeze',
                     'switching':{'low_history_threshold':5,'high_history_threshold':20,
                                  'cf_confidence_threshold':.5,'cf_weight':.5},'fixed_weights':{}}
        self.token='test-only-token-with-at-least-32-characters'

    def test_authentication_and_strict_input(self):
        with TestClient(create_app((self.engine,self.config),self.token)) as client:
            self.assertEqual(client.post('/recommendations',json={}).status_code,401)
            self.assertEqual(client.post('/recommendations',json={'k':51},headers={'X-Service-Token':self.token}).status_code,422)
            self.assertEqual(client.post('/recommendations',json={'email':'private'},headers={'X-Service-Token':self.token}).status_code,422)
            self.engine.signals.assert_not_called()

    def test_opt_out_discards_history_and_preferences(self):
        with TestClient(create_app((self.engine,self.config),self.token)) as client:
            response=client.post('/recommendations',json={'personalization':False,'event_count':5,
                'recent_items':[7],'seen_items':[7,8],'selected_categories':['9']},headers={'X-Service-Token':self.token})
            self.assertEqual(response.status_code,200)
            case=self.engine.signals.call_args.args[0]
            self.assertEqual(case.event_count,0)
            self.assertFalse(case.history or case.seen)
            self.assertEqual(self.engine.signals.call_args.kwargs['selected_categories'],[])
            self.assertFalse(response.json()['genai_used'])

    def test_missing_service_token_fails_closed(self):
        with self.assertRaises(ValueError):create_app(token='')

    def test_reviewed_description_is_separate_from_the_local_route_reason(self):
        identity = {'provider': 'groq_free', 'model': 'openai/gpt-oss-20b',
                    'catalogue': {'itemid': 7, 'properties': {'categoryid': '9'}}}
        output = {'description': 'Category ID 9.', 'source_properties': ['categoryid'],
                  'limitations': 'Anonymous codes.'}
        generated = {'identity': identity, 'cache_key': sha(identity), 'output': output,
                     'source_kind': 'generative_api', 'status': 'generated_pending_review'}
        review = {'cache_key': sha(identity), 'output_sha256': sha(output), 'approved': True,
                  'reviewer': 'fixture', 'rationale': 'Temporary fixture only'}
        self.config['serving_configuration'] = 'switching_with_genai'
        self.config['reviewed_descriptions'] = {'7': {'generation': generated, 'review': review}}
        with TestClient(create_app((self.engine,self.config),self.token)) as client:
            response = client.post('/recommendations', json={}, headers={'X-Service-Token': self.token})
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertTrue(body['genai_used'])
            self.assertFalse(body['genai_ranking_used'])  # Global popularity did not use text features.
            self.assertEqual(body['genai_description_count'], 1)
            self.assertEqual(body['items'][0]['catalogue_description'], 'Category ID 9.')
            self.assertEqual(body['items'][0]['reason'], 'Popular in the historical catalogue.')


if __name__=='__main__': unittest.main()

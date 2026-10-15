import sys
from pathlib import Path
import unittest
from pydantic import ValidationError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from service.demo import DemoRequest, recommend_demo
from switching.policy import PolicyConfig

POLICY=PolicyConfig(2,10,.25,.25)
def payload(profile=None, profiles=None):
    return DemoRequest(products=[
        {'id':'demo-a','title':'Cotton bag','category':'Carry','description':'cotton carry bag','attributes':[],'eligible':True},
        {'id':'demo-b','title':'Cotton tote','category':'Carry','description':'cotton carry tote','attributes':[],'eligible':True},
        {'id':'demo-c','title':'Tea mug','category':'Home','description':'ceramic tea mug','attributes':[],'eligible':True},
        {'id':'demo-d','title':'Tea cup','category':'Home','description':'ceramic tea cup','attributes':[],'eligible':False},
    ],profiles=profiles or [],profile=profile or {},k=4)

class DemoTests(unittest.TestCase):
    def test_no_data_fallback_is_honest_and_only_eligible(self):
        r=recommend_demo(payload(),POLICY)
        self.assertEqual(r['strategy'],'catalogue_fallback')
        self.assertEqual(r['fallback'],'insufficient_demo_evidence')
        self.assertEqual([i['productId'] for i in r['items']],['demo-a','demo-b','demo-c'])
        self.assertFalse(r['genai_used'])

    def test_content_uses_demo_features_and_filters_full_seen(self):
        r=recommend_demo(payload({'personalization':True,'event_count':1,'recent_items':['demo-a'],'seen_items':['demo-a']}),POLICY)
        self.assertEqual(r['strategy'],'content')
        self.assertEqual(r['items'][0]['productId'],'demo-b')
        self.assertNotIn('demo-a',[i['productId'] for i in r['items']])

    def test_cf_uses_actual_demo_profile_cooccurrence(self):
        r=recommend_demo(payload({'personalization':True,'event_count':12,'recent_items':['demo-a'],'seen_items':['demo-a']},[['demo-a','demo-c'],['demo-a','demo-c'],['demo-b']]),POLICY)
        self.assertEqual(r['strategy'],'item_cf')
        self.assertEqual(r['items'][0]['productId'],'demo-c')
        self.assertEqual(r['routing']['cf_confidence'],1)

    def test_consent_off_discards_preferences_and_history(self):
        p={'personalization':False,'event_count':12,'recent_items':['demo-a'],'seen_items':['demo-a'],'selected_categories':['Home']}
        r=recommend_demo(payload(p,[['demo-b'],['demo-b'],['demo-c']]),POLICY)
        self.assertEqual(r['strategy'],'global_popularity')
        self.assertEqual(r['routing']['history_event_count'],0)
        self.assertEqual(r['items'][0]['productId'],'demo-b')

    def test_preference_and_insufficient_cf_routes(self):
        r=recommend_demo(payload({'personalization':True,'selected_categories':['Home']},[['demo-b'],['demo-c']]),POLICY)
        self.assertEqual(r['strategy'],'category_popularity')
        self.assertEqual(r['items'][0]['productId'],'demo-c')
        r=recommend_demo(payload({'personalization':True,'event_count':12,'recent_items':['demo-a'],'seen_items':['demo-a']},[['demo-b']]),POLICY)
        self.assertEqual(r['strategy'],'hybrid_fallback')

    def test_research_ids_and_inconsistent_history_are_rejected(self):
        with self.assertRaises(ValidationError):payload(profiles=[['461686']])
        with self.assertRaises(ValidationError):payload({'event_count':1,'recent_items':['demo-a']})

if __name__=='__main__':unittest.main()

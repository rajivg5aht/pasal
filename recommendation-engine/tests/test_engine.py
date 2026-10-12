import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models.engine import RecommendationEngine
from models.collaborative.train_full import train as train_cf
from models.content.train_snapshot import train as train_content
from evaluation.common import Case
from switching.policy import PolicyConfig


class EngineTests(unittest.TestCase):
    def test_six_configurations_share_candidates_and_exclude_seen(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            events = pd.DataFrame([(1,1,10,"view"),(2,1,20,"view"),(3,2,20,"view"),
                                   (4,2,30,"view"),(5,3,40,"view")], columns=["timestamp","visitorid","itemid","event"])
            events.to_csv(root/'train.csv',index=False)
            records=[{"itemid":i,"as_of_ms":100,"source_sha256":"a"*64,
                      "properties":{"categoryid":"9","available":"0" if i==20 else "1"}} for i in [10,20,30,40]]
            (root/'catalogue.jsonl').write_text('\n'.join(json.dumps(r) for r in records))
            train_content(root/'catalogue.jsonl',root/'content',100)
            train_cf(root/'train.csv',root/'cf',100)
            engine=RecommendationEngine(events,100,root/'content',root/'cf')
            case=Case(1,2,(10,20),frozenset({10,20}),frozenset({30}))
            signals,confidence,selected=engine.signals(case)
            self.assertEqual(confidence,1)
            for name in ['global_popularity','category_popularity','tfidf','item_cf','fixed_hybrid','switching_without_genai']:
                recs,strategy=engine.predict(case,signals,confidence,selected,name,PolicyConfig(5,20,.5,.5),
                                  {'content':.25,'item_cf':.25,'global_popularity':.5})
                self.assertTrue(set(recs)<={30,40})
            cold=Case(9,0,(),frozenset(),frozenset({30}))
            s,c,p=engine.signals(cold)
            recs,strategy=engine.predict(cold,s,c,p,'switching_without_genai',PolicyConfig(5,20,.5,.5),{})
            self.assertEqual(strategy,'global_popularity')
            self.assertTrue(recs)
            with self.assertRaises(ValueError):
                engine.predict(cold,s,c,p,'switching_with_genai',PolicyConfig(5,20,.5,.5),{})
            policy = PolicyConfig(2, 10, .5, .5)
            for count, history, categories in [(0, (), []), (0, (), ['9']), (0, (), ['missing']),
                                                (1, (10,), []), (3, (10,), []), (20, (10,), []),
                                                (20, (999,), [])]:
                current = Case(1, count, history, frozenset(history), frozenset({30}))
                full = engine.signals(current, selected_categories=categories)
                lazy = engine.signals(current, selected_categories=categories, policy=policy)
                expected = engine.predict(current, *full, 'switching_without_genai', policy, {})
                actual = engine.predict(current, *lazy, 'switching_without_genai', policy, {})
                self.assertEqual(actual, expected)

    def test_rank_ties_are_stable_at_selection_boundary(self):
        self.assertEqual(RecommendationEngine.rank({i:1 for i in range(100,0,-1)},3),[1,2,3])
        with self.assertRaises(ValueError):
            RecommendationEngine.rank({1:float('nan')},1)


if __name__=='__main__': unittest.main()

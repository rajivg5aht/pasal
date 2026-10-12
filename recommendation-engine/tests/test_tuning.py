import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.content.train_snapshot import train as train_content
from models.collaborative.train_full import train as train_cf
from evaluation.tune_baselines import run


class TuningTests(unittest.TestCase):
    def test_validation_user_partitions_are_disjoint_and_all_six_models_assessed(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            events=[]
            for user,count in [(1,1),(2,1),(3,5),(4,5),(5,20),(6,20)]:
                for index in range(count): events.append((len(events)+1,user,10+10*(index%2),'view'))
            columns=['timestamp','visitorid','itemid','event']
            pd.DataFrame(events,columns=columns).to_csv(root/'train.csv',index=False)
            pd.DataFrame([(1000+i,user,30,'view') for i,user in enumerate(range(1,9))],columns=columns).to_csv(root/'validation.csv',index=False)
            (root/'catalogue.jsonl').write_text('\n'.join(json.dumps({'itemid':i,'as_of_ms':1000,'source_sha256':'a'*64,'properties':{'categoryid':'9','available':'1'}}) for i in [10,20,30]))
            train_content(root/'catalogue.jsonl',root/'content',1000)
            train_cf(root/'train.csv',root/'cf',1000)
            result=run(root/'train.csv',root/'validation.csv',root/'content',root/'cf',root/'results',2)
            self.assertEqual(result['genai_condition'],'not_evaluated')
            manifest=json.loads((root/'results/manifest.json').read_text())
            tuning={r['visitorid'] for r in manifest['sample'] if r['partition']=='tune'}
            assessment={r['visitorid'] for r in manifest['sample'] if r['partition']=='assessment'}
            self.assertEqual(len(tuning),4)
            self.assertFalse(tuning & assessment)
            rows=[json.loads(s) for s in (root/'results/per_user.jsonl').read_text().splitlines()]
            self.assertEqual(len(rows),24)
            self.assertEqual({r['visitorid'] for r in rows},assessment)
            self.assertTrue(all(r['latency_ms'] is None for r in rows))


if __name__=='__main__': unittest.main()

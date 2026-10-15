import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.sparse import eye

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.common import Case
from evaluation.final_holdout import require_complete, require_paired_validation, run, select_cases, verify
from evaluation.tune_baselines import CONFIGURATIONS
from models.content.train_snapshot import fingerprint


class FinalHoldoutTests(unittest.TestCase):
    def test_paired_validation_requires_current_inputs_and_complete_cases(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'manifest.json'
            source.write_text('{}')
            rows = [dict(visitorid=1, model=model, failure=None)
                    for model in CONFIGURATIONS + ['switching_with_genai']]
            records = root/'per_user.jsonl'
            records.write_text('\n'.join(map(json.dumps, rows)))
            (root/'exposure.jsonl').write_text('{"visitorid": 1}\n')
            report = root/'report.json'
            evidence = dict(status='partial_enrichment_validation_diagnostic_not_final_H2',
                density_manifest=None, exposure={'users': 1},
                inputs_sha256={str(source): fingerprint(source)},
                outputs_sha256={name: fingerprint(root/name) for name in ('per_user.jsonl', 'exposure.jsonl')})
            report.write_text(json.dumps(evidence))
            require_paired_validation(report, [source], {1})
            with self.assertRaisesRegex(ValueError, 'assessment partition'):
                require_paired_validation(report, [source], {2})
            source.write_text('{"new_treatment": true}')
            with self.assertRaisesRegex(ValueError, 'input mismatch'):
                require_paired_validation(report, [source], {1})
            source.write_text('{}')
            records.write_text('\n'.join(map(json.dumps, rows[:-1])))
            with self.assertRaisesRegex(ValueError, 'output mismatch'):
                require_paired_validation(report, [source], {1})
            evidence['outputs_sha256']['per_user.jsonl'] = fingerprint(records)
            report.write_text(json.dumps(evidence))
            with self.assertRaisesRegex(ValueError, 'seven configurations'):
                require_paired_validation(report, [source], {1})

    def test_incomplete_generation_cannot_freeze(self):
        evidence = dict(status='incomplete_sample', not_attempted=108, pending_review=0, reviewed_approved=11)
        with self.assertRaises(ValueError): require_complete(evidence)
        require_complete(dict(status='complete_sample', not_attempted=0, pending_review=0, reviewed_approved=1))

    def test_sampling_is_deterministic_and_does_not_drop_targetless_users(self):
        cases = [Case(i, 0, (), frozenset(), frozenset()) for i in range(20)]
        a, population = select_cases(cases, 5, 42)
        b, _ = select_cases(list(reversed(cases)), 5, 42)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 5)
        self.assertEqual(population['0'], 20)

    def test_fixture_runs_seven_models_and_both_exposure_populations(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            training = pd.DataFrame({'timestamp': [1, 2], 'visitorid': [1, 1], 'itemid': [1, 1], 'event': ['view']*2})
            outcomes = pd.DataFrame({'timestamp': [10, 11, 12, 13], 'visitorid': [1, 2, 1, 2], 'itemid': [2, 3, 2, 3], 'event': ['view']*4})
            training.to_csv(root/'train.csv', index=False)
            pd.concat([training, outcomes]).to_csv(root/'raw.csv', index=False)
            (root/'split.json').write_text(json.dumps({'test_start_ms': 10, 'effective_counts': [2, 0, 4],
                'legacy_validation_end_ms': 11, 'previously_exposed_test_events': 2}))
            for name in ['base', 'cf', 'enhanced']:
                (root/name).mkdir()
                (root/name/'manifest.json').write_text('{}')
            (root/'enhanced/reviewed_descriptions.json').write_text('{"2": {}}')
            class Engine:
                eligible = frozenset([1, 2, 3])
                content_ids = np.array([1, 2, 3])
                content = eye(3, format='csr')
                cf_manifest = {'train_sha256': fingerprint(root/'train.csv')}
                def __init__(self, *args): pass
                def signals(self, case): return {}, 0, []
                def predict(self, case, *args): return sorted(self.eligible-case.seen), 'global_popularity'
            paths = {'raw_events': 'raw.csv', 'train': 'train.csv', 'split': 'split.json',
                     'base': 'base/manifest.json', 'cf': 'cf/manifest.json', 'enriched': 'enhanced/manifest.json'}
            spec = {'status': 'frozen_before_holdout_materialization', 'paths': paths,
                'files_sha256': {v: fingerprint(root/v) for v in paths.values()},
                'config': {'cutoff_ms': 5, 'switching': {'low_history_threshold': 2, 'high_history_threshold': 10,
                    'cf_confidence_threshold': .25, 'cf_weight': .25}, 'fixed_weights': {}},
                'configurations': CONFIGURATIONS+['switching_with_genai'], 'per_cohort': 5, 'seed': 42, 'k': 10,
                'populations': {'full_15_percent': 'secondary', 'untouched_intersection': 'primary'}, 'limitations': ['fixture only']}
            frozen = root/'freeze.json'
            frozen.write_text(json.dumps(spec))
            with patch('evaluation.final_holdout.ROOT', root), patch('evaluation.final_holdout.RecommendationEngine', Engine):
                result = run(frozen, root/'result')
                self.assertEqual(result['populations']['untouched_intersection']['sampled_users'], 2)
                rows = [json.loads(s) for s in (root/'result/untouched_intersection-per_user.jsonl').read_text().splitlines()]
                self.assertEqual(len(rows), 14)
                self.assertEqual(len({r['model'] for r in rows}), 7)
                with self.assertRaises(FileExistsError): run(frozen, root/'result')
                (root/'train.csv').write_text('changed')
                with self.assertRaisesRegex(ValueError, 'Frozen input changed'): verify(spec)


if __name__ == '__main__': unittest.main()

import sys
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.analyze_exposure import compare
from genai.freeze_exposure_sample import freeze
from models.content.train_snapshot import fingerprint


class ExposureTests(unittest.TestCase):
    def setUp(self):
        self.config = {'cutoff_ms': 100, 'switching': {
            'low_history_threshold': 2, 'high_history_threshold': 10,
            'cf_confidence_threshold': .25, 'cf_weight': .25}}
        # User 4 has two repeated events: raw count excludes them from content.
        self.train = pd.DataFrame([(1, 1, 10), (2, 2, 10), (3, 3, 20),
                                   (4, 4, 30), (5, 4, 30), (6, 5, 40)],
                                  columns=['timestamp', 'visitorid', 'itemid'])
        self.records = [{'itemid': i, 'as_of_ms': 100, 'source_sha256': 'a'*64,
                         'properties': {'categoryid': str(i), 'available': '0' if i == 40 else '1'}}
                        for i in [10, 20, 30, 40]]

    def test_raw_counts_nested_deterministic_selection_and_unavailable_profiles(self):
        report, selections = compare(self.train, self.records, self.config, sizes=(1, 2))
        self.assertEqual(report['content_route_training_users'], 4)
        self.assertEqual(report['content_route_users_with_eligible_profile_item'], 3)
        self.assertEqual(selections['training_profile_support-1'], [10])
        self.assertEqual(selections['training_profile_support-2'], [10, 20])
        targeted = [r for r in report['comparisons'] if r['design'] == 'training_profile_support']
        self.assertEqual([r['content_route_training_users_exposed'] for r in targeted], [2, 3])
        self.assertEqual(targeted[0]['content_route_training_user_exposure_fraction'], .5)
        self.assertEqual(selections, compare(self.train, self.records[::-1], self.config, sizes=(1, 2))[1])
        self.assertTrue(set(selections['uniform_catalogue-1']) <= set(selections['uniform_catalogue-2']))

    def test_future_duplicate_and_catalogue_cutoff_fail_closed(self):
        future = self.train.copy()
        future.loc[0, 'timestamp'] = 100
        with self.assertRaises(ValueError):
            compare(future, self.records, self.config, sizes=(1,))
        with self.assertRaises(ValueError):
            compare(self.train, self.records+self.records[:1], self.config, sizes=(1,))
        with self.assertRaises(ValueError):
            compare(self.train, [{**r, 'as_of_ms': 101} for r in self.records], self.config, sizes=(1,))

    def test_no_content_users_reports_undefined_exposure(self):
        config = {**self.config, 'switching': {**self.config['switching'], 'low_history_threshold': 1}}
        report, _ = compare(self.train, self.records, config, sizes=(1,))
        self.assertEqual(report['content_route_training_users'], 0)
        self.assertTrue(all(r['content_route_training_user_exposure_fraction'] is None for r in report['comparisons']))

    def test_frozen_sample_preserves_source_and_rejects_selection_tampering(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'catalogue.jsonl'
            source.write_text(''.join(json.dumps(r)+'\n' for r in self.records))
            report, selections = compare(self.train, self.records, self.config, sizes=(1,))
            (root/'selections.json').write_text(json.dumps(selections))
            report['selections_sha256'] = fingerprint(root/'selections.json')
            report['inputs_sha256'] = {str(source): fingerprint(source)}
            (root/'report.json').write_text(json.dumps(report))
            manifest = freeze(root, source, root/'sample', size=1)
            self.assertEqual(manifest['itemids'], [10])
            self.assertEqual(json.loads((root/'sample/catalogue.jsonl').read_text()), self.records[0])
            with self.assertRaises(FileExistsError):
                freeze(root, source, root/'sample', size=1)
            (root/'selections.json').write_text('{}')
            with self.assertRaises(ValueError):
                freeze(root, source, root/'altered', size=1)


if __name__ == '__main__':
    unittest.main()

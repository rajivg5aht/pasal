import copy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.analyze_human_review import FIELDS, digest, summarize, validate


class HumanReviewAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.template = {'rubric': {'fixture': 'Do not infer semantics'}, 'instructions': ['Independent ratings'],
                         'cases': [{'case_id': 'Q001', 'historical_source_properties': {'categoryid': '7'},
                                    'generated_output': {'description': 'Category code 7'},
                                    'ratings': dict.fromkeys(FIELDS)},
                                   {'case_id': 'Q002', 'historical_source_properties': {},
                                    'generated_output': {'description': 'Semantics unavailable'},
                                    'ratings': dict.fromkeys(FIELDS)}]}
        self.returned = {**copy.deepcopy(self.template), 'reviewer_code': 'R1', 'review_date': '2026-10-13'}

    def test_rejects_changed_sources_duplicate_cases_and_invalid_ratings(self):
        for mutate in (
            lambda r: r['cases'][0]['generated_output'].update(description='Invented brand'),
            lambda r: r['cases'].append(copy.deepcopy(r['cases'][0])),
            lambda r: r['cases'][0]['ratings'].update(clarity_1_to_5=True),
            lambda r: r['cases'][0]['ratings'].update(usefulness_1_to_5=6),
            lambda r: r['cases'][0]['ratings'].update(supported_assertions=-1),
            lambda r: r['cases'][0]['ratings'].update(unsupported_assertions=1, unsupported_claim_severity='none'),
        ):
            with self.subTest(mutate=mutate):
                record = copy.deepcopy(self.returned)
                mutate(record)
                with self.assertRaises(ValueError):
                    validate(self.template, record)

    def test_missing_counts_do_not_enter_denominator_and_disagreements_remain(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            template_path = root/'reviewer-template.json'
            template_path.write_text(json.dumps(self.template))
            (root/'manifest.json').write_text(json.dumps({'template_sha256': digest(template_path),
                                                         'failed_attempts_not_rateable': 8}))
            first = copy.deepcopy(self.returned)
            first['cases'][0]['ratings'].update(supported_assertions=3, unsupported_assertions=1, clarity_1_to_5=4)
            # A supported count with a missing unsupported count must not inflate consistency.
            first['cases'][1]['ratings'].update(supported_assertions=100)
            second = copy.deepcopy(self.returned)
            second['reviewer_code'] = 'R2'
            second['cases'][0]['ratings'].update(supported_assertions=0, unsupported_assertions=0, clarity_1_to_5=2)
            files = [root/'r1.json', root/'r2.json']
            for path, data in zip(files, [first, second]):
                path.write_text(json.dumps(data))
            result = summarize(root, files)
            self.assertEqual(result['per_reviewer']['R1']['factual_consistency']['pooled_assertion_fraction'], .75)
            self.assertEqual(result['per_reviewer']['R1']['missing_by_field']['unsupported_assertions'], 1)
            self.assertIsNone(result['per_reviewer']['R2']['factual_consistency']['pooled_assertion_fraction'])
            self.assertEqual(result['per_reviewer']['R2']['factual_consistency']['zero_assessable_cases'], 1)
            comparison = result['pairwise_exact_comparisons'][0]['fields']['clarity_1_to_5']
            self.assertEqual(comparison, {'paired_cases': 1, 'exact_matches': 0, 'disagreement_cases': ['Q001']})
            with self.assertRaises(ValueError):
                summarize(root, [files[0], files[0]])
            template_path.write_text('{}')
            with self.assertRaises(ValueError):
                summarize(root, files)

    def test_empty_ratings_remain_empty(self):
        code, cases = validate(self.template, self.returned)
        self.assertEqual(code, 'R1')
        self.assertTrue(all(value is None for ratings in cases.values() for value in ratings.values()))


if __name__ == '__main__':
    unittest.main()

from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.final_statistics import analyze, holm


class FinalStatisticsTests(unittest.TestCase):
    def rows(self):
        return [{'model': m, 'visitorid': u, 'cohort': '0' if u < 3 else '1-4', 'ndcg': 0.0}
                for m in ['fixed_hybrid', 'switching_without_genai', 'switching_with_genai'] for u in range(4)]

    def test_holm_preserves_original_order_and_monotonicity(self):
        np.testing.assert_allclose(holm([.04, .01, .03]), [.06, .03, .06])
        for invalid in [[float('nan')], [-.1], [1.1]]:
            with self.assertRaises(ValueError): holm(invalid)

    def test_zero_differences_are_not_significant(self):
        result = analyze(self.rows(), resamples=20, permutations=31)
        for row in result['comparisons']:
            self.assertEqual(row['holm_p'], 1)
            self.assertEqual(row['paired_bootstrap_95_percentile_interval'], [0, 0])
            self.assertEqual(row['ties'], row['users'])
        self.assertEqual(result['comparisons'][0]['users'], 1)
        self.assertEqual(result['comparisons'][1]['users'], 4)

    def test_macro_weighting_and_matched_population(self):
        rows = self.rows()
        for r in rows:
            if r['model'] == 'switching_with_genai' and r['visitorid'] == 3:
                r['ndcg'] = 1
        report = analyze(rows, resamples=20, permutations=31)['comparisons'][1]
        self.assertEqual(report['equal_cohort_mean_ndcg_difference'], .5)
        with self.assertRaises(ValueError): analyze(rows[:-1])
        with self.assertRaises(ValueError): analyze(rows + [rows[0]])

    def test_high_history_scores_do_not_change_approved_hypothesis_results(self):
        rows = self.rows()
        for model in ['fixed_hybrid', 'switching_without_genai', 'switching_with_genai']:
            rows.append({'model': model, 'visitorid': 100, 'cohort': '20+',
                         'ndcg': 1.0 if model == 'switching_with_genai' else 0.0})
        for result in analyze(rows, resamples=20, permutations=31)['comparisons']:
            self.assertEqual(result['equal_cohort_mean_ndcg_difference'], 0)
            self.assertNotIn('20+', result['primary_cohorts'])


if __name__ == '__main__': unittest.main()

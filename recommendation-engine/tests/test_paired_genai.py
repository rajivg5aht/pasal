from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.paired_genai import paired_interval
from genai.quality_report import wilson


class PairedGenAITests(unittest.TestCase):
    def test_pairing_uses_id_and_preserves_zero_effect(self):
        rows = [{'visitorid': i, 'model': model, 'cohort': '0' if i < 3 else '1-4', 'ndcg': .5}
                for model in ['switching_with_genai', 'switching_without_genai'] for i in range(6)]
        result = paired_interval(list(reversed(rows)))
        self.assertEqual(result['mean_ndcg_difference_equal_cohort_weight'], 0)
        self.assertEqual(result['bootstrap_95_percentile_interval'], [0, 0])
        with self.assertRaises(ValueError):
            paired_interval(rows[:-1])

    def test_quality_interval_is_uncertain_even_with_no_observed_failures(self):
        low, high = wilson(32, 32)
        self.assertLess(low, .95)
        self.assertAlmostEqual(high, 1)
        self.assertIsNone(wilson(0, 0))


if __name__ == '__main__':
    unittest.main()

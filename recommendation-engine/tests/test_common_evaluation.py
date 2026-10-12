from pathlib import Path
import sys
import unittest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.common import prepare_cases, evaluate, summarize, ranking_metrics, cohort


class CommonEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.train = pd.DataFrame([(1, 1, 10), (3, 1, 10), (2, 1, 11)],
                                  columns=["timestamp", "visitorid", "itemid"])
        self.future = pd.DataFrame([(5, 1, 12), (6, 2, 99)], columns=self.train.columns)

    def test_zero_history_and_raw_event_count_are_preserved(self):
        cases = prepare_cases(self.train, self.future, 5)
        self.assertEqual([c.event_count for c in cases], [3, 0])
        self.assertEqual(cases[0].history, (11, 10))
        self.assertEqual([cohort(n) for n in [0, 1, 4, 5, 19, 20]], ["0", "1-4", "1-4", "5-19", "5-19", "20+"])

    def test_future_history_is_rejected(self):
        with self.assertRaises(ValueError):
            prepare_cases(self.train, self.future, 3)

    def test_invalid_and_failed_predictions_count_as_zero(self):
        cases = prepare_cases(self.train, self.future, 5)
        rows = evaluate(cases, {"good": lambda c, e, k: [12],
                                "bad": lambda c, e, k: [99]}, {10, 11, 12})
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(r["failure"] is not None for r in rows), 2)
        all_good = next(r for r in summarize(rows, {10, 11, 12}) if r["model"] == "good" and r["cohort"] == "all")
        self.assertEqual(all_good["users"], 2)
        self.assertEqual(all_good["recall"], .5)
        self.assertEqual(rows[2]["target_count"], 1)
        self.assertEqual(rows[2]["eligible_target_count"], 0)

    def test_map_and_short_list_penalty(self):
        result = ranking_metrics([3, 2], {2, 4}, 10)
        self.assertEqual(result["map"], .25)
        self.assertEqual(result["precision"], .1)
        self.assertEqual(result["hit_rate"], 1)

    def test_sampling_does_not_depend_on_model_coverage(self):
        first = prepare_cases(self.train, self.future, 5, 1, seed=42)
        second = prepare_cases(self.train.iloc[::-1], self.future.iloc[::-1], 5, 1, seed=42)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

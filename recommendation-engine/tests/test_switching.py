from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from switching.policy import PolicyConfig, route, combine, recommend


class SwitchingTests(unittest.TestCase):
    def setUp(self):
        self.config = PolicyConfig(5, 20, .5, .6)

    def test_every_branch_and_threshold_boundary(self):
        self.assertEqual([route(n, .8, [], self.config) for n in [0, 1, 4, 5, 19, 20]],
                         ["global_popularity", "content", "content", "cf_popularity_hybrid", "cf_popularity_hybrid", "item_cf"])
        self.assertEqual(route(0, 0, ["cat"], self.config), "category_popularity")
        self.assertEqual(route(20, .49, [], self.config), "hybrid_fallback")
        self.assertEqual(route(20, .5, [], self.config), "item_cf")

    def test_normalization_excludes_seen_before_scaling(self):
        scores = combine({"a": {1: 1000, 2: 2}, "b": {3: 5}}, {"a": .5, "b": .5}, {2, 3})
        self.assertEqual(scores, {2: .5, 3: .5})

    def test_recommendations_are_filtered_and_trace_fallback(self):
        signals = {"global_popularity": {1: 5, 2: 3}, "category_popularity": {}, "content": {}, "item_cf": {}}
        result = recommend(0, {1}, {1, 2}, ["cat"], 0, signals, self.config)
        self.assertEqual(result["items"], [2])
        self.assertEqual(result["strategy"], "global_popularity")
        self.assertIsNotNone(result["fallback_reason"])

    def test_invalid_configuration_and_scores_fail(self):
        with self.assertRaises(ValueError):
            PolicyConfig(5, 5, .5, .5)
        with self.assertRaises(ValueError):
            combine({"a": {1: float("nan")}}, {"a": 1}, {1})


if __name__ == "__main__":
    unittest.main()

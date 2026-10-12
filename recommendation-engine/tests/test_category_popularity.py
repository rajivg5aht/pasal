from pathlib import Path
import sys
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models.popularity.category_popularity import CategoryPopularity


class CategoryPopularityTests(unittest.TestCase):
    def setUp(self):
        self.events = pd.DataFrame({"itemid": [1,2,3,4], "event": ["view","transaction","transaction","addtocart"],
                                    "timestamp": [1,2,3,4]})
        self.model = CategoryPopularity.fit(self.events, {1:"A",2:"B",3:"A",4:"A"}, 5)

    def test_category_ranking_and_full_seen_filter(self):
        result = self.model.recommend(["A"], {3}, {1,2,3,4})
        self.assertEqual(result.item_ids, [4,1])
        self.assertEqual(result.strategy, "category_popularity")

    def test_zero_history_fallback_and_deterministic_ties(self):
        result = self.model.recommend([], set(), {1,2,3,4})
        self.assertEqual(result.item_ids, [2,3,4,1])
        self.assertEqual(result.strategy, "global_popularity")

    def test_availability_and_no_silent_forced_fallback(self):
        result = self.model.recommend(["B"], set(), {1,3,4}, fallback=False)
        self.assertEqual(result.item_ids, [])

    def test_future_or_unknown_events_rejected(self):
        with self.assertRaises(ValueError):
            CategoryPopularity.fit(self.events, {}, 4)
        bad = self.events.copy()
        bad.loc[0,"event"] = "unknown"
        with self.assertRaises(ValueError):
            CategoryPopularity.fit(bad, {}, 5)


if __name__ == "__main__":
    unittest.main()

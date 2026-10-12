from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models.collaborative.train_full import fit


class FullCFTests(unittest.TestCase):
    def setUp(self):
        self.events = pd.DataFrame([(1, 1, 10, "view"), (2, 1, 20, "view"),
            (3, 2, 10, "transaction"), (4, 2, 30, "view"), (5, 3, 40, "view"),
            (6, 1, 10, "view")], columns=["timestamp", "visitorid", "itemid", "event"])

    def test_cosine_matches_dense_reference_with_all_users_and_no_self_links(self):
        result, ids, counts = fit(self.events, 10, top_k=3, block_size=1)
        expected = np.array([[0, 1/np.sqrt(2), 1/np.sqrt(2), 0],
                             [1/np.sqrt(2), 0, 0, 0], [1/np.sqrt(2), 0, 0, 0], [0,0,0,0]])
        np.testing.assert_allclose(result.toarray(), expected, atol=1e-7)
        self.assertEqual(counts["training_users"], 3)
        self.assertEqual(counts["isolated_items"], 1)
        self.assertEqual(ids.tolist(), [10,20,30,40])

    def test_ties_and_block_sizes_are_deterministic(self):
        first, _, _ = fit(self.events, 10, top_k=1, block_size=1)
        second, _, _ = fit(self.events.iloc[::-1], 10, top_k=1, block_size=4)
        np.testing.assert_allclose(first.toarray(), second.toarray())
        self.assertEqual(first[0].indices.tolist(), [1])

    def test_future_events_rejected(self):
        with self.assertRaises(ValueError):
            fit(self.events, 6)


if __name__ == "__main__":
    unittest.main()

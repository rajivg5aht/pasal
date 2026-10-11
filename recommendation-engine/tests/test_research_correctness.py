"""Small adversarial fixtures independent of Retailrocket or the frozen test set."""
import math
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_utils import (binary_ranking_metrics, build_user_histories,
                            select_profile_history, top_positive_indices, validate_matrix_ids)
from evaluation.evaluate_content_comparison import recommend_content


class ResearchCorrectnessTests(unittest.TestCase):
    def test_history_uses_last_timestamp_not_file_order_or_first_occurrence(self):
        events = pd.DataFrame({"visitorid": [1]*5, "itemid": [10, 20, 10, 30, 40],
                               "timestamp": [100, 200, 500, 400, 300]})
        histories, seen = build_user_histories(events, 2)
        self.assertEqual(histories[1], [30, 10])
        self.assertEqual(seen[1], {10, 20, 30, 40})

    def test_users_do_not_share_histories(self):
        frame = pd.DataFrame({"visitorid": [1,2,1], "itemid": [10,20,30], "timestamp": [3,4,5]})
        histories, seen = build_user_histories(frame, 1)
        self.assertEqual(histories, {2: [20], 1: [30]})
        self.assertEqual(seen, {1: {10,30}, 2: {20}})

    def test_hybrid_excludes_items_older_than_profile_window(self):
        history = pd.DataFrame({"itemid": range(1, 23), "timestamp": range(1, 23)})
        profile, seen = select_profile_history(history, 20)
        self.assertEqual(len(profile), 20)
        self.assertNotIn(1, set(profile.itemid))
        self.assertIn(1, seen)
        ids = np.arange(1, 24)
        scores = np.ones(23)
        scores[np.isin(ids, list(seen))] = -np.inf
        self.assertEqual(ids[top_positive_indices(scores, ids)].tolist(), [23])

    def test_score_ties_are_independent_of_matrix_row_order(self):
        ids = np.array([40,10,30,20])
        self.assertEqual(ids[top_positive_indices(np.ones(4), ids, 2)].tolist(), [10,20])

    def test_nonpositive_and_nonfinite_scores_are_not_recommended(self):
        scores = [0, -1, np.nan, np.inf, -np.inf, .1]
        self.assertEqual(top_positive_indices(scores, range(6)).tolist(), [5])
        self.assertEqual(top_positive_indices([], []).tolist(), [])

    def test_binary_metrics_hand_calculated(self):
        p,r,n = binary_ranking_metrics([5,7,9], {5,9,11}, 3)
        self.assertAlmostEqual(p, 2/3)
        self.assertAlmostEqual(r, 2/3)
        self.assertAlmostEqual(n, 1.5 / (1 + 1/math.log2(3) + .5))

    def test_empty_and_short_lists_count_missing_slots_as_zero(self):
        self.assertEqual(binary_ranking_metrics([], {1}, 10), (0,0,0))
        self.assertEqual(binary_ranking_metrics([1], {1}, 10), (.1,1,1))
        self.assertEqual(binary_ranking_metrics([1], set(), 10), (0,0,0))

    def test_duplicates_rejected_and_k_respected(self):
        with self.assertRaises(ValueError):
            binary_ranking_metrics([1,1], {1}, 10)
        self.assertEqual(binary_ranking_metrics([1,2,3], {3}, 2), (0,0,0))

    def test_invalid_artifact_mapping_rejected(self):
        for ids in [[1], [1,1]]:
            with self.assertRaises(ValueError):
                validate_matrix_ids(csr_matrix(np.eye(2)), ids)
        with self.assertRaises(ValueError):
            validate_matrix_ids(csr_matrix([[np.nan]]), [1])

    def test_content_retains_metadata_only_candidates_and_excludes_all_seen(self):
        ids = [10,20,30,40]
        matrix = csr_matrix([[1.,0.], [1.,0.], [1.,0.], [0.,1.]])
        mapping = {item:i for i,item in enumerate(ids)}
        # 30 has metadata but no training interaction. It remains a valid
        # development candidate; temporal eligibility is a separate protocol.
        self.assertEqual(recommend_content(1,[10],{10,20},matrix,ids,mapping), [30])
        self.assertEqual(recommend_content(2,[],set(),matrix,ids,mapping), [])


if __name__ == "__main__":
    unittest.main()

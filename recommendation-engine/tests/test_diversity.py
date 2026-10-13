from pathlib import Path
import sys
import unittest

from scipy.sparse import csr_matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.analyze_density import diversity


class DiversityTests(unittest.TestCase):
    def test_identical_orthogonal_and_missing_vectors(self):
        matrix = csr_matrix([[1., 0.], [1., 0.], [0., 1.], [0., 0.]])
        rows = {10: 0, 20: 1, 30: 2, 40: 3}
        self.assertEqual(diversity([10, 20], matrix, rows)['value'], 0)
        self.assertEqual(diversity([10, 30], matrix, rows)['value'], 1)
        partial = diversity([10, 30, 40, 99], matrix, rows)
        self.assertEqual(partial, {'value': 1., 'valid_pairs': 1, 'total_pairs': 6})
        self.assertIsNone(diversity([40, 99], matrix, rows)['value'])


if __name__ == '__main__':
    unittest.main()

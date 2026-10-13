from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.benchmark_stack import validate_response


class StackBenchmarkTests(unittest.TestCase):
    def test_hydration_duplicates_and_unexpected_personalization_are_not_successes(self):
        item = {'itemid': 10, 'product': {'_id': 10, 'available': True}}
        data = {'strategy': 'global_popularity', 'items': [item]}
        self.assertEqual(validate_response('/api/recommendations', data), 1)
        for invalid in [
            {**data, 'items': [item, item]},
            {**data, 'strategy': 'content'},
            {**data, 'items': [{**item, 'product': {'_id': 20, 'available': True}}]},
            {**data, 'items': [{**item, 'product': {'_id': 10, 'available': False}}]},
        ]:
            with self.assertRaises(ValueError):
                validate_response('/api/recommendations', invalid)


if __name__ == '__main__':
    unittest.main()

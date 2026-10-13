from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import threading
import unittest

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from service.capacity import RecommendationCapacity


class CapacityTests(unittest.TestCase):
    def test_admission_rejects_excess_and_releases_after_exception(self):
        gate = RecommendationCapacity(active=1, waiting=0)
        with self.assertRaisesRegex(RuntimeError, 'fixture'):
            with gate.slot():
                with self.assertRaises(HTTPException) as rejected:
                    with gate.slot():
                        self.fail('Over capacity')
                self.assertEqual(rejected.exception.status_code, 503)
                self.assertEqual(rejected.exception.headers['Retry-After'], '1')
                raise RuntimeError('fixture')
        with gate.slot():
            pass

    def test_wait_timeout_releases_admission_without_releasing_active_slot(self):
        gate = RecommendationCapacity(active=1, waiting=1, wait_seconds=0)
        with gate.slot():
            for _ in range(2):
                with self.assertRaises(HTTPException):
                    with gate.slot():
                        self.fail('Active slot must remain occupied')
        with gate.slot():
            pass

    def test_waiter_runs_when_active_computation_finishes(self):
        gate = RecommendationCapacity(active=1, waiting=1, wait_seconds=2)
        entered = threading.Event()
        attempting = threading.Event()
        def worker():
            attempting.set()
            with gate.slot() as wait:
                entered.set()
                return wait
        with ThreadPoolExecutor(max_workers=1) as pool:
            with gate.slot():
                future = pool.submit(worker)
                self.assertTrue(attempting.wait(1))
                self.assertFalse(entered.is_set())
            self.assertGreaterEqual(future.result(timeout=3), 0)
            self.assertTrue(entered.is_set())


if __name__ == '__main__':
    unittest.main()

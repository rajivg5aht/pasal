"""Bound both active recommendation computations and short-lived waiting requests."""
from contextlib import contextmanager
import threading
import time

from fastapi import HTTPException


class RecommendationCapacity:
    def __init__(self, active=2, waiting=2, wait_seconds=0.5):
        if type(active) is not int or active < 1 or type(waiting) is not int or waiting < 0:
            raise ValueError('Capacity limits must be positive active/nonnegative waiting integers')
        if not 0 <= wait_seconds <= 2:
            raise ValueError('Wait must be bounded to at most two seconds')
        self.admission = threading.BoundedSemaphore(active + waiting)
        self.execution = threading.BoundedSemaphore(active)
        self.wait_seconds = wait_seconds

    @contextmanager
    def slot(self):
        started = time.perf_counter()
        if not self.admission.acquire(blocking=False):
            raise HTTPException(503, 'Recommendation capacity busy; try again shortly',
                                headers={'Retry-After': '1'})
        acquired = False
        try:
            acquired = self.execution.acquire(timeout=self.wait_seconds)
            if not acquired:
                raise HTTPException(503, 'Recommendation wait limit exceeded; try again shortly',
                                    headers={'Retry-After': '1'})
            yield (time.perf_counter() - started) * 1000
        finally:
            if acquired:
                self.execution.release()
            self.admission.release()

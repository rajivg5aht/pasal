"""Category-conditioned popularity baseline, independent of switching policy.

The caller supplies point-in-time category mappings and candidate eligibility.
Category selection uses explicit preferences/history, never held-out targets.
"""
from dataclasses import dataclass

import pandas as pd

EVENT_WEIGHTS = {"view": 1.0, "addtocart": 3.0, "transaction": 5.0}


@dataclass
class PopularityResult:
    item_ids: list[int]
    strategy: str
    reason: str


class CategoryPopularity:
    def __init__(self, scores, categories):
        self.scores = scores
        self.categories = {int(item): str(category) for item, category in categories.items()}
        self.ranked = sorted(scores, key=lambda item: (-scores[item], item))

    @classmethod
    def fit(cls, training_events, categories, cutoff_ms):
        columns = ["itemid", "event", "timestamp"]
        if training_events[columns].isna().any().any():
            raise ValueError("Training IDs, events and timestamps must be present")
        if (training_events.timestamp >= cutoff_ms).any():
            raise ValueError("Training events must precede the declared cutoff")
        weights = training_events.event.map(EVENT_WEIGHTS)
        if weights.isna().any():
            raise ValueError("Unknown event type; do not silently assign a weight")
        scores = training_events.assign(weight=weights).groupby("itemid").weight.sum().to_dict()
        return cls({int(item): float(score) for item, score in scores.items()}, categories)

    def recommend(self, selected_categories, seen_items, eligible_items, k=10, fallback=True):
        if k < 1:
            raise ValueError("k must be positive")
        selected = set(map(str, selected_categories))
        seen, eligible = set(map(int, seen_items)), set(map(int, eligible_items))
        candidates = [item for item in self.ranked if item in eligible and item not in seen]
        if selected:
            ranked = [item for item in candidates if self.categories.get(item) in selected]
            if ranked:
                return PopularityResult(ranked[:k], "category_popularity", "Explicitly selected catalogue categories")
            if not fallback:
                return PopularityResult([], "category_popularity", "No eligible scored item in selected categories")
        elif not fallback:
            return PopularityResult([], "category_popularity", "No category evidence supplied")
        return PopularityResult(candidates[:k], "global_popularity", "No usable category evidence; configured fallback")

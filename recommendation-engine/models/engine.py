"""Shared scoring contracts for offline comparisons and the recommendation API."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import load_npz

from models.content.train_snapshot import fingerprint
from research_utils import validate_matrix_ids
from switching.policy import PolicyConfig, normalize, route


def load_artifact(directory, cutoff_ms):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["cutoff_exclusive_ms"] != cutoff_ms:
        raise ValueError("Artifact cutoff mismatch")
    for name, expected in manifest["artifacts_sha256"].items():
        if fingerprint(directory / name) != expected:
            raise ValueError("Artifact fingerprint mismatch")
    matrix = load_npz(directory / "matrix.npz").tocsr()
    items = pd.read_csv(directory / "items.csv", dtype={"categoryid": "str", "available": "str"})
    validate_matrix_ids(matrix, items.itemid.to_numpy())
    return matrix, items, manifest


class RecommendationEngine:
    def __init__(self, training, cutoff_ms, content_dir, cf_dir):
        if training.empty or training[["timestamp", "itemid", "event"]].isna().any().any():
            raise ValueError("Invalid training events")
        if (training.timestamp >= cutoff_ms).any():
            raise ValueError("Training crosses prediction origin")
        weights = training.event.map({"view": 1., "addtocart": 3., "transaction": 5.})
        if weights.isna().any():
            raise ValueError("Unexpected event type")
        self.popularity = training.assign(weight=weights).groupby("itemid").weight.sum().to_dict()
        self.content, items, self.content_manifest = load_artifact(content_dir, cutoff_ms)
        self.cf, cf_items, self.cf_manifest = load_artifact(cf_dir, cutoff_ms)
        self.content_ids, self.cf_ids = items.itemid.to_numpy(), cf_items.itemid.to_numpy()
        if self.cf.shape[1] != len(self.cf_ids) or self.cf.diagonal().any():
            raise ValueError("CF graph must be square without self links")
        self.content_rows = {int(item): i for i, item in enumerate(self.content_ids)}
        self.cf_rows = {int(item): i for i, item in enumerate(self.cf_ids)}
        self.categories = items.dropna(subset=["categoryid"]).set_index("itemid").categoryid.to_dict()
        unavailable = set(items.loc[items.available == "0", "itemid"])
        self.eligible = frozenset((set(self.popularity) | set(self.content_ids)) - unavailable)
        self.popularity = {i: v for i, v in self.popularity.items() if i in self.eligible}
        self.content_eligible = np.array([i in self.eligible for i in self.content_ids])

    def signals(self, case, selected_categories=None, policy=None):
        candidates = self.eligible if not case.seen else self.eligible - case.seen
        selected = (set(selected_categories) if selected_categories is not None else
                    {self.categories[i] for i in case.history if i in self.categories})
        cf_rows = [self.cf_rows[i] for i in case.history if i in self.cf_rows]
        usable = sum(self.cf.indptr[i + 1] > self.cf.indptr[i] for i in cf_rows)
        confidence = usable / len(case.history) if case.history else 0.0
        required = {'global_popularity', 'category_popularity', 'content', 'item_cf'}
        if policy is not None:
            strategy = route(case.event_count, confidence, selected if case.event_count == 0 else [], policy)
            required = ({'item_cf', 'global_popularity'} if strategy in {'cf_popularity_hybrid', 'hybrid_fallback'}
                        else {'category_popularity', 'global_popularity'} if strategy == 'category_popularity'
                        else {strategy})
        pop = normalize(self.popularity, candidates) if 'global_popularity' in required else {}
        cat = (normalize({i: v for i, v in self.popularity.items() if self.categories.get(i) in selected}, candidates)
               if 'category_popularity' in required else {})
        content = {}
        history_rows = [self.content_rows[i] for i in case.history if i in self.content_rows]
        if history_rows and 'content' in required:
            profile = np.asarray(self.content[history_rows].mean(axis=0)).ravel()
            norm = np.linalg.norm(profile)
            if norm:
                values = np.asarray(self.content @ (profile / norm)).ravel()
                values[~self.content_eligible] = 0
                for item in case.seen:
                    if item in self.content_rows:
                        values[self.content_rows[item]] = 0
                positive = np.flatnonzero(values > 0)
                content = normalize({int(self.content_ids[i]): values[i] for i in positive}, candidates)
        cf = {}
        if cf_rows and 'item_cf' in required:
            values = np.asarray(self.cf[cf_rows].sum(axis=0)).ravel()
            positive = np.flatnonzero(values > 0)
            cf = normalize({int(self.cf_ids[i]): values[i] for i in positive}, candidates)
        return {"global_popularity": pop, "category_popularity": cat,
                "content": content, "item_cf": cf}, float(confidence), selected

    @staticmethod
    def rank(scores, k):
        if k < 1:
            raise ValueError("k must be positive")
        ids = np.fromiter(scores.keys(), dtype=np.int64, count=len(scores))
        values = np.fromiter(scores.values(), dtype=np.float64, count=len(scores))
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("Invalid ranking scores")
        keep = np.flatnonzero(values > 0)
        if len(keep) > k:
            boundary = np.partition(values[keep], -k)[-k]
            keep = keep[values[keep] >= boundary]
        order = np.lexsort((ids[keep], -values[keep]))[:k]
        return ids[keep[order]].astype(int).tolist()

    @staticmethod
    def blend(signals, weights):
        if not weights or any(not np.isfinite(w) or w < 0 for w in weights.values()) or not np.isclose(sum(weights.values()), 1):
            raise ValueError("Nonnegative weights must sum to one")
        scores = {}
        for name, weight in weights.items():
            if name not in signals:
                raise ValueError("Unknown component")
            if weight:
                for item, value in signals[name].items():
                    scores[item] = scores.get(item, 0) + weight * value
        return scores

    def predict(self, case, signals, confidence, selected, configuration, policy, weights, k=10):
        if configuration == "fixed_hybrid":
            return self.rank(self.blend(signals, weights), k), "fixed_hybrid"
        if configuration == "switching_with_genai":
            if (self.content_manifest.get('kind') != 'historical_properties_plus_reviewed_generative_text'
                    or self.content_manifest.get('approved_items', 0) < 1):
                raise ValueError('GenAI configuration requires a verified enriched artifact')
        if configuration in {"switching_without_genai", "switching_with_genai"}:
            strategy = route(case.event_count, confidence, selected if case.event_count == 0 else [], policy)
            if strategy in {"cf_popularity_hybrid", "hybrid_fallback"}:
                mixed = self.blend(signals, {"item_cf": policy.cf_weight, "global_popularity": 1-policy.cf_weight})
                return self.rank(mixed, k), strategy
        else:
            strategy = {"tfidf": "content"}.get(configuration, configuration)
        if strategy not in signals:
            raise ValueError("Unsupported configuration; GenAI needs a separately verified enriched model")
        if strategy == "category_popularity" and not signals[strategy]:
            strategy = "global_popularity"
        return self.rank(signals[strategy], k), strategy

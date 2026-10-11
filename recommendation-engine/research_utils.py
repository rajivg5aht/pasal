"""Shared correctness rules for development recommenders (not a final protocol)."""
import math

import numpy as np


def build_user_histories(events, max_items=20):
    """Recent unique items by LAST timestamp; retain ALL items for exclusion.

    Equal timestamps retain input order. Interaction cohort counts must be based
    on event counts, never the truncated profiles returned here.
    """
    if max_items < 1:
        raise ValueError("max_items must be positive")
    required = ["timestamp", "visitorid", "itemid"]
    if events[required].isna().any().any():
        raise ValueError("History timestamps and IDs must not be missing")
    seen = events.groupby("visitorid", sort=False).itemid.agg(set).to_dict()
    recent = (
        events.sort_values("timestamp", kind="stable")
        .drop_duplicates(["visitorid", "itemid"], keep="last")
        .groupby("visitorid", sort=False).tail(max_items)
    )
    histories = recent.groupby("visitorid", sort=False).itemid.agg(list).to_dict()
    return histories, seen


def select_profile_history(history, max_items=20):
    """Return weighted profile rows plus the complete user's seen set."""
    if max_items < 1:
        raise ValueError("max_items must be positive")
    seen = set(history.itemid.astype(int))
    profile = (history.sort_values("timestamp", kind="stable")
               .drop_duplicates("itemid", keep="last").tail(max_items))
    return profile, seen


def validate_matrix_ids(matrix, item_ids, name="content"):
    ids = np.asarray(item_ids)
    if matrix.shape[0] != len(ids):
        raise ValueError(f"{name}: matrix rows do not match item IDs")
    if len(np.unique(ids)) != len(ids):
        raise ValueError(f"{name}: duplicate item IDs")
    if not np.isfinite(matrix.data).all() or (matrix.data < 0).any():
        raise ValueError(f"{name}: matrix must contain finite nonnegative scores")


def top_positive_indices(scores, item_ids, k=10):
    """Rank finite positive scores; break ALL ties by ascending item ID."""
    if k < 1:
        raise ValueError("k must be positive")
    scores = np.asarray(scores).ravel()
    ids = np.asarray(item_ids)
    if len(scores) != len(ids):
        raise ValueError("Scores and item IDs must align")
    candidates = np.flatnonzero(np.isfinite(scores) & (scores > 0))
    order = np.lexsort((ids[candidates], -scores[candidates]))
    return candidates[order[:k]]


def binary_ranking_metrics(recommendations, relevant_items, k=10):
    """Binary Precision@K, Recall@K, NDCG@K; missing slots score zero."""
    if k < 1:
        raise ValueError("k must be positive")
    recommended = list(recommendations)[:k]
    if len(set(recommended)) != len(recommended):
        raise ValueError("Duplicate recommendations would inflate ranking metrics")
    relevant = set(relevant_items)
    hits = [int(item in relevant) for item in recommended]
    dcg = sum(hit / math.log2(rank + 2) for rank, hit in enumerate(hits))
    idcg = sum(1 / math.log2(rank + 2) for rank in range(min(len(relevant), k)))
    return sum(hits) / k, sum(hits) / len(relevant) if relevant else 0.0, dcg / idcg if idcg else 0.0

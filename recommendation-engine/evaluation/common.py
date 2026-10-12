"""Model-independent chronological evaluation; no outcome-driven user eligibility."""
from dataclasses import dataclass
import time

import numpy as np
import pandas as pd

from research_utils import binary_ranking_metrics, build_user_histories


def cohort(event_count):
    if event_count < 0:
        raise ValueError("Negative history size")
    return "0" if event_count == 0 else "1-4" if event_count < 5 else "5-19" if event_count < 20 else "20+"


@dataclass(frozen=True)
class Case:
    visitorid: int
    event_count: int
    history: tuple
    seen: frozenset
    targets: frozenset


def prepare_cases(training, outcomes, cutoff_ms, max_users=None, seed=42):
    """One prediction at cutoff; no validation interactions update the history.

    Targets include future/unavailable items to retain end-to-end denominator.
    Repeat consumption of already-seen items is outside the discovery task;
    users with only repeated targets remain, with zero metrics, and are flagged.
    """
    for frame in (training, outcomes):
        if frame[["timestamp", "visitorid", "itemid"]].isna().any().any():
            raise ValueError("Missing timestamps or identifiers")
    if (training.timestamp >= cutoff_ms).any() or (outcomes.timestamp < cutoff_ms).any():
        raise ValueError("Training/outcome timestamps cross the prediction origin")
    if max_users is not None and max_users < 1:
        raise ValueError("max_users must be positive")
    histories, seen = build_user_histories(training)
    counts = training.groupby("visitorid").size().to_dict()
    targets = outcomes.groupby("visitorid").itemid.agg(set).to_dict()
    users = np.array(sorted(targets), dtype=np.int64)
    if max_users is not None and len(users) > max_users:
        users = np.sort(np.random.default_rng(seed).choice(users, max_users, replace=False))
    return [Case(int(u), int(counts.get(u, 0)), tuple(histories.get(u, [])),
                 frozenset(seen.get(u, set())), frozenset(targets[u] - seen.get(u, set()))) for u in users]


def ranking_metrics(recommended, relevant, k):
    p, r, n = binary_ranking_metrics(recommended, relevant, k)
    hits = [int(i in relevant) for i in list(recommended)[:k]]
    ap = sum(sum(hits[:j + 1]) / (j + 1) for j, hit in enumerate(hits) if hit)
    return {"precision": p, "recall": r, "ndcg": n,
            "map": ap / min(len(relevant), k) if relevant else 0.0,
            "hit_rate": float(any(hits))}


def evaluate(cases, recommenders, eligible_items, k=10):
    """recommender(case, eligible_unseen, k) returns ordered integer IDs.

    Invalid outputs fail closed for that user and are recorded, not silently
    repaired or removed from denominators. Exceptions expose type only.
    """
    if k < 1 or not cases or not recommenders:
        raise ValueError("Positive k, cases and recommenders required")
    if len({case.visitorid for case in cases}) != len(cases):
        raise ValueError("Duplicate evaluation users")
    eligible = frozenset(eligible_items)
    rows = []
    for case in cases:
        candidates = eligible if not case.seen else eligible - case.seen
        for name, recommender in recommenders.items():
            started = time.perf_counter()
            failure = None
            try:
                recs = list(recommender(case, candidates, k))
                if len(recs) > k or len(set(recs)) != len(recs) or not set(recs) <= candidates:
                    raise ValueError("Invalid ranked output")
            except Exception as error:
                failure, recs = type(error).__name__, []
            elapsed = (time.perf_counter() - started) * 1000
            eligible_targets = case.targets & candidates
            rows.append({"model": name, "visitorid": case.visitorid,
                         "cohort": cohort(case.event_count), "history_events": case.event_count,
                         "target_count": len(case.targets), "eligible_target_count": len(eligible_targets),
                         "targetless": not bool(case.targets), "recommendations": recs,
                         "failure": failure, "latency_ms": elapsed,
                         **ranking_metrics(recs, case.targets, k),
                         **{"eligible_" + key: value for key, value in ranking_metrics(recs, eligible_targets, k).items()}})
    return rows


def summarize(rows, eligible_items):
    if not rows:
        raise ValueError("No evaluation rows")
    frame = pd.DataFrame(rows)
    summaries = []
    for name, group in frame.groupby("model", sort=True):
        for label in ["all", "0", "1-4", "5-19", "20+"]:
            subset = group if label == "all" else group[group.cohort == label]
            recommended = set(i for recs in subset.recommendations for i in recs)
            summaries.append({"model": name, "cohort": label, "users": len(subset),
                "failures": int(subset.failure.notna().sum()),
                "targetless_users": int(subset.targetless.sum()),
                "served_users": int(subset.recommendations.map(bool).sum()),
                "catalogue_coverage": len(recommended) / len(eligible_items) if len(eligible_items) else 0.0,
                "p95_latency_ms": float(subset.latency_ms.dropna().quantile(.95)) if subset.latency_ms.notna().any() else None,
                **{m: float(subset[m].mean()) if len(subset) else None
                   for m in ["precision", "recall", "ndcg", "map", "hit_rate"]}})
    return summaries

"""Explicit Figure 5 routing; thresholds are supplied by validation tuning."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PolicyConfig:
    low_history_threshold: int
    high_history_threshold: int
    cf_confidence_threshold: float
    cf_weight: float

    def __post_init__(self):
        if not (type(self.low_history_threshold) is int and type(self.high_history_threshold) is int
                and 1 <= self.low_history_threshold < self.high_history_threshold):
            raise ValueError("Require integer thresholds 1 <= low < high")
        for value in (self.cf_confidence_threshold, self.cf_weight):
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Confidence threshold and hybrid weight must be in [0, 1]")


def route(event_count, cf_confidence, selected_categories, config):
    if type(event_count) is not int or event_count < 0:
        raise ValueError("History size must be a nonnegative event count")
    if not math.isfinite(cf_confidence) or not 0 <= cf_confidence <= 1:
        raise ValueError("Invalid CF evidence confidence")
    if event_count == 0:
        return "category_popularity" if selected_categories else "global_popularity"
    if event_count < config.low_history_threshold:
        return "content"
    if event_count < config.high_history_threshold:
        return "cf_popularity_hybrid"
    if cf_confidence >= config.cf_confidence_threshold:
        return "item_cf"
    return "hybrid_fallback"


def normalize(scores, candidates):
    """Max-normalize nonnegative evidence on the SAME eligible unseen universe."""
    values = {int(item): float(score) for item, score in scores.items() if item in candidates}
    if any(not math.isfinite(v) or v < 0 for v in values.values()):
        raise ValueError("Nonfinite or negative evidence")
    peak = max(values.values(), default=0)
    return {item: score / peak for item, score in values.items() if score > 0} if peak else {}


def combine(signals, weights, candidates):
    if set(signals) != set(weights) or not signals:
        raise ValueError("Weights and signals must match")
    if any(not math.isfinite(w) or w < 0 for w in weights.values()) or not math.isclose(sum(weights.values()), 1):
        raise ValueError("Nonnegative weights must sum to one")
    scores = {}
    for name, signal in signals.items():
        for item, value in normalize(signal, candidates).items():
            scores[item] = scores.get(item, 0) + weights[name] * value
    return scores


def recommend(event_count, seen, eligible, selected_categories, cf_confidence,
              signals, config, k=10, use_genai=False):
    """Return auditable decisions; generation changes content evidence only.

    The caller computes cf_confidence as the fraction of profile items with
    usable CF neighbours. No held-out interactions or metrics are inputs here.
    """
    if k < 1:
        raise ValueError("k must be positive")
    strategy = route(event_count, cf_confidence, selected_categories, config)
    candidates = frozenset(eligible) - frozenset(seen)
    required = {"global_popularity", "category_popularity", "item_cf", "content"}
    if not required <= set(signals):
        raise ValueError("Missing required evidence signals")
    if strategy in {"cf_popularity_hybrid", "hybrid_fallback"}:
        scores = combine({"cf": signals["item_cf"], "pop": signals["global_popularity"]},
                         {"cf": config.cf_weight, "pop": 1 - config.cf_weight}, candidates)
    else:
        scores = normalize(signals[strategy], candidates)
    fallback = None
    if strategy == "category_popularity" and not scores:
        fallback = "no_eligible_category_evidence"
        strategy = "global_popularity"
        scores = normalize(signals[strategy], candidates)
    ranked = sorted((item for item, score in scores.items() if score > 0), key=lambda item: (-scores[item], item))[:k]
    return {"items": ranked, "strategy": strategy, "fallback_reason": fallback,
            "history_events": event_count, "cf_confidence": cf_confidence,
            "genai_condition": bool(use_genai), "candidate_count": len(candidates)}

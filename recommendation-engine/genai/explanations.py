"""Truthful local routing reasons plus optional reviewed, genuinely generated text."""
from .enrichment import approved_text, sha

REASONS = {
    "global_popularity": "Popular in the historical catalogue.",
    "category_popularity": "Popular within your selected categories.",
    "content": "Selected using similarity to your previous item interactions.",
    "item_cf": "Selected using historical item co-interaction patterns.",
    "fixed_hybrid": "Selected using the configured combination of recommendation signals.",
    "cf_popularity_hybrid": "Selected using collaborative and popularity evidence.",
    "hybrid_fallback": "Selected using the hybrid fallback because collaborative evidence was insufficient.",
}


def explain(itemid, strategy, generated=None, review=None):
    if strategy not in REASONS:
        raise ValueError("An actual recorded recommendation strategy is required")
    result = {"itemid": itemid, "strategy": strategy, "reason": REASONS[strategy],
              "catalogue_description": None, "description_source": "unavailable"}
    if generated is not None and review is not None:
        if (generated.get("source_kind") != "generative_api" or
                sha(generated["identity"]) != generated.get("cache_key")):
            raise ValueError("Invalid generation provenance")
        if generated["identity"]["catalogue"]["itemid"] != itemid:
            raise ValueError("Explanation provenance belongs to a different item")
        if generated["identity"]["provider"] not in {"groq_free", "openai_responses"}:
            raise ValueError("Fixture descriptions cannot be served as GenAI")
        result.update(catalogue_description=approved_text(generated, review),
                      description_source="reviewed_generative_api", cache_key=generated["cache_key"])
    return result

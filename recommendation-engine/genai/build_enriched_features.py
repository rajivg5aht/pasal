"""Export matched non-GenAI/GenAI feature tables from reviewed API outputs.

Missing, failed or unreviewed generations fall back to the SAME base features.
Quality counts are operational evidence, not a claim of recommendation benefit.
"""
import argparse
import csv
import json
from pathlib import Path
import re

try:
    from .enrichment import approved_text, sha, validate_catalogue
except ImportError:
    from enrichment import approved_text, sha, validate_catalogue


def base_content(record):
    # Preserve property/value identity; no inferred semantics or product names.
    return " ".join(f"prop{key}_val_{re.sub(r'[^a-zA-Z0-9]+', '_', value).strip('_')}"
                    for key, value in sorted(record["properties"].items()))


def export_features(catalogue_path, cache_dir, reviews_path, output_dir, model):
    records = [validate_catalogue(json.loads(line)) for line in Path(catalogue_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records or len({r["itemid"] for r in records}) != len(records):
        raise ValueError("A nonempty catalogue with unique item IDs is required")
    if len({r["as_of_ms"] for r in records}) != 1:
        raise ValueError("Feature tables must share one explicit metadata cutoff")
    by_id = {r["itemid"]: r for r in records}
    reviews = {}
    if reviews_path is not None:
        for line in Path(reviews_path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            review = json.loads(line)
            if review["cache_key"] in reviews:
                raise ValueError("Duplicate review decisions")
            reviews[review["cache_key"]] = review
    accepted = {}
    counts = {"matching_api_records": 0, "failed_or_rejected": 0,
              "generated_pending_review": 0, "approved_items": 0,
              "input_tokens_reported": 0, "output_tokens_reported": 0,
              "records_without_token_usage": 0}
    cache_hashes = {}
    for path in sorted(Path(cache_dir).glob("*.json")):
        if not re.fullmatch(r"[0-9a-f]{64}\.json", path.name):
            continue
        cached = json.loads(path.read_text(encoding="utf-8"))
        identity = cached["identity"]
        record = identity["catalogue"]
        if identity["model"] != model or by_id.get(record["itemid"]) != record:
            continue
        if identity["provider"] not in {"openai_responses", "groq_free"} or cached.get("source_kind") != "generative_api":
            raise ValueError("Test/simulated outputs cannot be used as actual GenAI evidence")
        if sha(identity) != cached["cache_key"] or path.stem != cached["cache_key"]:
            raise ValueError("Cache fingerprint mismatch")
        cache_hashes[path.stem] = sha(cached)
        counts["matching_api_records"] += 1
        usage = cached.get("provider_metadata", {}).get("usage", {})
        if "input_tokens" not in usage or "output_tokens" not in usage:
            counts["records_without_token_usage"] += 1
        else:
            counts["input_tokens_reported"] += usage["input_tokens"]
            counts["output_tokens_reported"] += usage["output_tokens"]
        if cached["status"] != "generated_pending_review":
            counts["failed_or_rejected"] += 1
            continue
        review = reviews.get(path.stem)
        if not review or review.get("approved") is not True:
            counts["generated_pending_review"] += 1
            continue
        text = approved_text(cached, review)
        if record["itemid"] in accepted:
            raise ValueError("Multiple approved generations for one item; select one version explicitly")
        accepted[record["itemid"]] = text
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    for enriched in [False, True]:
        name = "features_with_genai.csv" if enriched else "features_without_genai.csv"
        with (output_dir / name).open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["itemid", "content"])
            writer.writeheader()
            for record in sorted(records, key=lambda r: r["itemid"]):
                content = base_content(record)
                if enriched and record["itemid"] in accepted:
                    content += " " + accepted[record["itemid"]]
                writer.writerow({"itemid": record["itemid"], "content": content})
    counts["approved_items"] = len(accepted)
    counts["catalogue_items"] = len(records)
    counts["fallback_items"] = len(records) - len(accepted)
    manifest = {
        "status": "paired_features_exported_not_a_ranking_evaluation",
        "model": model, "catalogue_sha256": sha(records), "reviews_sha256": sha(reviews),
        "cache_record_sha256": cache_hashes, "as_of_ms": records[0]["as_of_ms"],
        "counts": counts,
        "limitations": ["Schema/citation checks do not prove factual consistency",
                        "Human rating study and paid-call cost reconciliation are separate",
                        "H2 requires equivalent switching configurations and paired cohort evaluation"],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    print(json.dumps(export_features(args.catalogue, args.cache, args.reviews, args.output_dir, args.model), indent=2))

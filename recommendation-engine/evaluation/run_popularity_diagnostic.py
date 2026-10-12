"""Development-only common evaluator smoke run; never opens final test data."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.common import prepare_cases, evaluate, summarize


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(train_path, validation_path, output, max_users=1000):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Use a new diagnostic directory")
    train = pd.read_csv(train_path)
    validation = pd.read_csv(validation_path)
    cutoff = int(validation.timestamp.min())
    weights = train.event.map({"view": 1, "addtocart": 3, "transaction": 5})
    if weights.isna().any():
        raise ValueError("Unexpected event type")
    scores = train.assign(weight=weights).groupby("itemid").weight.sum()
    ranking = sorted(scores.index, key=lambda item: (-scores[item], item))
    eligible = frozenset(ranking)
    cases = prepare_cases(train, validation, cutoff, max_users=max_users)

    def popularity(case, candidates, k):
        result = []
        for item in ranking:
            if item in candidates:
                result.append(int(item))
                if len(result) == k:
                    break
        return result

    rows = evaluate(cases, {"global_popularity": popularity}, eligible)
    summaries = summarize(rows, eligible)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "per_user.jsonl").open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
    (output / "summary.json").write_text(json.dumps(summaries, indent=2, allow_nan=False))
    manifest = {"purpose": "development_diagnostic_not_final_results", "seed": 42,
                "cutoff_ms": cutoff, "users": [case.visitorid for case in cases],
                "inputs": {str(p): fingerprint(p) for p in [train_path, validation_path]},
                "source_sha256": {str(p): fingerprint(p) for p in [Path(__file__), Path(__file__).with_name("common.py")]},
                "limitations": ["Legacy duration split; not final event-count protocol",
                                "Candidates restricted to training-observed IDs; no availability property applied",
                                "Validation interaction targets; zero-history retained; no onboarding preferences",
                                "Only popularity, not the seven-configuration experiment"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=Path("data/splits/train.csv"))
    parser.add_argument("--validation", type=Path, default=Path("data/splits/validation.csv"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-users", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(run(args.train, args.validation, args.output, args.max_users), indent=2))

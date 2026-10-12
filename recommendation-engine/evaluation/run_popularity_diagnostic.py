"""Development-only common evaluator smoke run; never opens final test data."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd
import numpy as np
from scipy.sparse import load_npz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.common import prepare_cases, evaluate, summarize
from research_utils import top_positive_indices, validate_matrix_ids


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(train_path, validation_path, output, max_users=1000, content_dir=None):
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
    content_manifest = None
    if content_dir is not None:
        content_dir = Path(content_dir)
        content_manifest = json.loads((content_dir / "manifest.json").read_text())
        if content_manifest["cutoff_exclusive_ms"] != cutoff:
            raise ValueError("Content and event prediction cutoffs do not match")
        for name, expected in content_manifest["artifacts_sha256"].items():
            if fingerprint(content_dir / name) != expected:
                raise ValueError("Content artifact hash mismatch")
        matrix = load_npz(content_dir / "matrix.npz").tocsr()
        items = pd.read_csv(content_dir / "items.csv", dtype={"categoryid": "str", "available": "str"})
        ids = items.itemid.to_numpy()
        validate_matrix_ids(matrix, ids)
        row_by_id = {int(item): index for index, item in enumerate(ids)}
        categories = items.dropna(subset=["categoryid"]).set_index("itemid").categoryid.to_dict()
        unavailable = set(items.loc[items.available == "0", "itemid"])
        # Unknown availability is admitted, explicitly; observed unavailable is excluded.
        eligible = frozenset((set(ranking) | set(ids)) - unavailable)
    cases = prepare_cases(train, validation, cutoff, max_users=max_users)

    def popularity(case, candidates, k):
        result = []
        for item in ranking:
            if item in candidates:
                result.append(int(item))
                if len(result) == k:
                    break
        return result

    recommenders = {"global_popularity": popularity}
    if content_dir is not None:
        def content(case, candidates, k):
            history_rows = [row_by_id[i] for i in case.history if i in row_by_id]
            if not history_rows:
                return []
            profile = np.asarray(matrix[history_rows].mean(axis=0)).ravel()
            norm = np.linalg.norm(profile)
            if norm == 0:
                return []
            values = np.asarray(matrix @ (profile / norm)).ravel()
            values[[i for i, item in enumerate(ids) if item not in candidates]] = 0
            return [int(ids[i]) for i in top_positive_indices(values, ids, k)]

        def category_popularity(case, candidates, k):
            selected = {categories[i] for i in case.history if i in categories}
            ranked = [int(i) for i in ranking if i in candidates and categories.get(i) in selected][:k]
            return ranked if ranked else popularity(case, candidates, k)

        recommenders.update(category_popularity=category_popularity, tfidf=content)
    rows = evaluate(cases, recommenders, eligible)
    summaries = summarize(rows, eligible)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "per_user.jsonl").open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
    (output / "summary.json").write_text(json.dumps(summaries, indent=2, allow_nan=False))
    manifest = {"purpose": "development_diagnostic_not_final_results", "seed": 42,
                "cutoff_ms": cutoff, "users": [case.visitorid for case in cases],
                "inputs": {str(p): fingerprint(p) for p in [train_path, validation_path]},
                "content_manifest": content_manifest,
                "source_sha256": {str(p): fingerprint(p) for p in [Path(__file__), Path(__file__).with_name("common.py")]},
                "limitations": ["Development validation only; no final test analysis",
                                "With content: train-observed or snapshot-known IDs, excluding explicit available=0; unknown availability admitted",
                                "Without content: training-observed IDs only; no availability property applied",
                                "Validation interaction targets; zero-history retained; no onboarding preferences",
                                "Category baseline uses historical categories; zero-history falls back globally",
                                "Partial baseline diagnostic, not the seven-configuration experiment"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=Path("data/splits/train.csv"))
    parser.add_argument("--validation", type=Path, default=Path("data/splits/validation.csv"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-users", type=int, default=1000)
    parser.add_argument("--content-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.train, args.validation, args.output, args.max_users, args.content_dir), indent=2))

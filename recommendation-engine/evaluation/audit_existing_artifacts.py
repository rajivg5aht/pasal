"""Read-only audit of existing development artifacts; never reads test.csv.

Run from any directory. The JSON report is new evidence, not final evaluation.
"""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.sparse import load_npz

ROOT = Path(__file__).resolve().parents[2]


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def audit():
    processed = ROOT / "data/processed"
    train_path = ROOT / "data/splits/train.csv"
    validation_path = ROOT / "data/splits/validation.csv"
    train = pd.read_csv(train_path, usecols=["timestamp", "visitorid", "itemid", "event"])
    validation = pd.read_csv(validation_path, usecols=["timestamp", "visitorid", "itemid"])
    cutoff = int(validation.timestamp.min())
    # Only timestamp/count integrity is inspected in the raw event file.
    raw_times = pd.read_csv(ROOT / "data/raw/events.csv", usecols=["timestamp"])
    report = {
        "scope": "Existing development artifacts; no final test file read or model training",
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__, "scipy": scipy.__version__,
                     "scikit_learn": sklearn.__version__},
        "raw_event_count": len(raw_times),
        "splits": {}, "content_models": {}, "fingerprints": {},
    }
    for name, frame, path in [("train", train, train_path), ("validation", validation, validation_path)]:
        report["splits"][name] = {
            "rows": len(frame), "event_percentage": 100 * len(frame) / len(raw_times),
            "min_timestamp": int(frame.timestamp.min()), "max_timestamp": int(frame.timestamp.max()),
            "timestamp_sorted": bool(frame.timestamp.is_monotonic_increasing),
            "adjacent_timestamp_reversals": int((frame.timestamp.diff() < 0).sum()),
            "unique_users": int(frame.visitorid.nunique()), "unique_items": int(frame.itemid.nunique()),
        }
        report["fingerprints"][str(path.relative_to(ROOT))] = fingerprint(path)
    report["train_strictly_before_validation"] = bool(train.timestamp.max() < validation.timestamp.min())
    catalogs = []
    for suffix in ["", "_enhanced"]:
        paths = [processed / f"item_tfidf_matrix{suffix}.npz",
                 processed / f"item_tfidf_ids{suffix}.csv",
                 processed / f"item_tfidf_vectorizer{suffix}.joblib"]
        matrix = load_npz(paths[0]).tocsr()
        ids = pd.read_csv(paths[1]).itemid.to_numpy()
        # Local project artifacts only: do not load untrusted pickle/joblib files.
        vectorizer = joblib.load(paths[2])
        features = pd.read_csv(processed / f"item_features{suffix}.csv", usecols=["itemid", "content"])
        rows = np.linspace(0, len(ids) - 1, 32, dtype=int)
        lookup = features.set_index("itemid").content
        reconstructed = vectorizer.transform(lookup.loc[ids[rows]].tolist())
        delta = matrix[rows] - reconstructed
        max_error = float(abs(delta).max())
        catalogs.append(set(map(int, ids)))
        report["content_models"][suffix or "original"] = {
            "shape": list(matrix.shape), "nnz": int(matrix.nnz), "dtype": str(matrix.dtype),
            "unique_ids": len(set(ids)), "duplicate_ids": int(len(ids) - len(set(ids))),
            "rows_match_ids": bool(matrix.shape[0] == len(ids)),
            "finite": bool(np.isfinite(matrix.data).all()),
            "zero_rows": int((matrix.getnnz(axis=1) == 0).sum()),
            "reconstruction_rows_checked": len(rows), "reconstruction_max_error": max_error,
            "reconstruction_matches_tolerance_1e_6": max_error < 1e-6,
        }
        for path in paths:
            report["fingerprints"][str(path.relative_to(ROOT))] = fingerprint(path)
    popularity_path = processed / "popularity_ranking.csv"
    popularity = pd.read_csv(popularity_path)
    pop_ids = set(map(int, popularity.itemid))
    catalogs.append(pop_ids)
    expected = train.assign(score=train.event.map({"view": 1, "addtocart": 3, "transaction": 5})).groupby("itemid").score.sum()
    scores = popularity.set_index("itemid").popularity_score.sort_index()
    report["popularity"] = {
        "items": len(popularity), "training_item_ids_match": pop_ids == set(train.itemid),
        "training_scores_match": bool(scores.equals(expected.sort_index())),
        "items_without_content": len(pop_ids - catalogs[0]),
    }
    report["catalog_union_size"] = len(set.union(*catalogs))
    report["content_id_sets_equal"] = catalogs[0] == catalogs[1]
    report["fingerprints"][str(popularity_path.relative_to(ROOT))] = fingerprint(popularity_path)
    cf = load_npz(processed / "item_cf_similarities_sample.npz").tocsr()
    cf_ids = pd.read_csv(processed / "item_cf_item_ids_sample.csv").itemid
    report["collaborative_sample"] = {
        "shape": list(cf.shape), "unique_ids": int(cf_ids.nunique()),
        "shape_matches_ids": bool(cf.shape == (len(cf_ids), len(cf_ids))),
        "finite": bool(np.isfinite(cf.data).all()), "nonnegative": bool((cf.data >= 0).all()),
        "diagonal_zero": bool((cf.diagonal() == 0).all()),
        "max_neighbors": int(np.diff(cf.indptr).max()),
        "training_item_coverage": len(cf_ids) / train.itemid.nunique(),
    }
    report["saved_metrics"] = {p.name: pd.read_csv(p).to_dict("records") for p in processed.glob("*metrics.csv")}
    report["property_columns"] = pd.read_csv(processed / "item_properties.csv", nrows=0).columns.tolist()
    report["metadata_temporal_audit"] = {"cutoff_exclusive": int(validation.timestamp.min()), "files": {}}
    for path in sorted((ROOT / "data/raw").glob("item_properties_part*.csv")):
        total = future = 0
        first_seen = {}
        for chunk in pd.read_csv(path, usecols=["timestamp", "itemid"], chunksize=500_000):
            total += len(chunk)
            future += int((chunk.timestamp >= cutoff).sum())
            for item, timestamp in chunk.groupby("itemid").timestamp.min().items():
                first_seen[item] = min(first_seen.get(item, timestamp), timestamp)
        report["metadata_temporal_audit"]["files"][path.name] = {
            "rows": total, "rows_at_or_after_validation_start": future,
        }
        report["metadata_temporal_audit"].setdefault("_first_seen", {})
        for item, timestamp in first_seen.items():
            seen = report["metadata_temporal_audit"]["_first_seen"]
            seen[item] = min(seen.get(item, timestamp), timestamp)
    first_seen = report["metadata_temporal_audit"].pop("_first_seen")
    report["metadata_temporal_audit"]["content_items_first_observed_after_cutoff"] = int(sum(
        first_seen.get(item, 0) >= cutoff for item in catalogs[0]
    ))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output path; previous audit evidence is preserved.")
    result = audit()
    serialized = json.dumps(result, indent=2, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(serialized)
    print(f"Audit saved: {args.output.resolve()}")

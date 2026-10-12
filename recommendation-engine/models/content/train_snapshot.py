"""Train versioned content features from one validated historical snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import save_npz
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from genai.enrichment import validate_catalogue
from genai.build_enriched_features import base_content
from research_utils import validate_matrix_ids


def fingerprint(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def train(catalogue, output, cutoff_ms, min_df=2, max_features=100000):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Use a new artifact version")
    ids, documents, categories, availability = [], [], [], []
    with Path(catalogue).open(encoding="utf-8") as stream:
        for line in stream:
            record = validate_catalogue(json.loads(line))
            if record["as_of_ms"] != cutoff_ms:
                raise ValueError("Snapshot does not match the declared training cutoff")
            ids.append(record["itemid"])
            documents.append(base_content(record))
            categories.append(record["properties"].get("categoryid"))
            availability.append(record["properties"].get("available"))
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Snapshot IDs must be nonempty and unique")
    vectorizer = TfidfVectorizer(lowercase=False, token_pattern=r"(?u)\b\w+\b",
                                 norm="l2", dtype=np.float32, min_df=min_df, max_features=max_features)
    matrix = vectorizer.fit_transform(documents).tocsr()
    validate_matrix_ids(matrix, ids)
    output.mkdir(parents=True, exist_ok=False)
    save_npz(output / "matrix.npz", matrix)
    joblib.dump(vectorizer, output / "vectorizer.joblib")
    pd.DataFrame({"itemid": ids, "categoryid": categories, "available": availability}).to_csv(output / "items.csv", index=False)
    manifest = {"kind": "historical_property_tfidf_not_genai", "cutoff_exclusive_ms": cutoff_ms,
                "catalogue_sha256": fingerprint(catalogue), "source_sha256": fingerprint(__file__),
                "rows": matrix.shape[0], "features": matrix.shape[1], "nonzeros": matrix.nnz,
                "zero_vector_rows": int((np.diff(matrix.indptr) == 0).sum()),
                "min_df": min_df, "max_features": max_features,
                "availability_counts": {"available": availability.count("1"),
                                        "unavailable": availability.count("0"),
                                        "unknown": sum(v not in ("0", "1") for v in availability)},
                "limitations": ["Property identifiers have no inferred semantic meanings",
                                 "No ranking evaluation or GenAI benefit is established by training"]}
    manifest["artifacts_sha256"] = {name: fingerprint(output / name) for name in ["matrix.npz", "vectorizer.joblib", "items.csv"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cutoff-ms", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(train(args.catalogue, args.output, args.cutoff_ms), indent=2))

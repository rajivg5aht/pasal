"""Full-training binary item cosine, computed in bounded item blocks."""
import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, csr_matrix, save_npz

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from models.content.train_snapshot import fingerprint


def fit(events, cutoff_ms, top_k=50, block_size=128, progress=False):
    if top_k < 1 or block_size < 1 or events.empty:
        raise ValueError("Require training events and positive block/neighbor limits")
    if events[["timestamp", "visitorid", "itemid", "event"]].isna().any().any():
        raise ValueError("Missing training evidence")
    if (events.timestamp >= cutoff_ms).any():
        raise ValueError("Training must precede prediction origin")
    if not events.event.isin(["view", "addtocart", "transaction"]).all():
        raise ValueError("Unknown event type")
    pairs = events[["visitorid", "itemid"]].drop_duplicates()
    users, user_ids = pd.factorize(pairs.visitorid, sort=True)
    items, item_ids = pd.factorize(pairs.itemid, sort=True)
    item_ids = np.asarray(item_ids, dtype=np.int64)
    item_user = coo_matrix((np.ones(len(pairs), dtype=np.float32), (items, users)),
                           shape=(len(item_ids), len(user_ids))).tocsr()
    norms = np.sqrt(np.asarray(item_user.power(2).sum(axis=1)).ravel())
    normalized = item_user.multiply((1 / norms)[:, None]).tocsr()
    transpose = normalized.T.tocsc()
    # Preallocate only final top-k graph, not the full item-by-item product.
    capacity = len(item_ids) * min(top_k, len(item_ids))
    indices = np.empty(capacity, dtype=np.int32)
    data = np.empty(capacity, dtype=np.float32)
    indptr = np.zeros(len(item_ids) + 1, dtype=np.int64)
    offset = 0
    started = time.perf_counter()
    for start in range(0, len(item_ids), block_size):
        end = min(start + block_size, len(item_ids))
        block = (normalized[start:end] @ transpose).tocsr()
        for local, row in enumerate(range(start, end)):
            lo, hi = block.indptr[local:local + 2]
            cols, scores = block.indices[lo:hi], block.data[lo:hi]
            valid = (cols != row) & (scores > 0)
            cols, scores = cols[valid], scores[valid]
            order = np.lexsort((item_ids[cols], -scores))[:top_k]
            cols, scores = cols[order], scores[order]
            count = len(cols)
            indices[offset:offset + count], data[offset:offset + count] = cols, scores
            offset += count
            indptr[row + 1] = offset
        if progress and (start == 0 or (start // block_size) % 100 == 0):
            print(f"CF items {end:,}/{len(item_ids):,}; elapsed {time.perf_counter()-started:.1f}s", flush=True)
    matrix = csr_matrix((data[:offset], indices[:offset], indptr), shape=(len(item_ids), len(item_ids)))
    matrix.sort_indices()
    return matrix, item_ids, {"training_users": len(user_ids), "unique_user_item_pairs": len(pairs),
                             "training_events": len(events), "items": len(item_ids),
                             "isolated_items": int((np.diff(indptr) == 0).sum())}


def train(train_path, output, cutoff_ms, top_k=50, block_size=128):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Use a new model version")
    events = pd.read_csv(train_path, usecols=["timestamp", "visitorid", "itemid", "event"])
    matrix, ids, counts = fit(events, cutoff_ms, top_k, block_size, progress=True)
    output.mkdir(parents=True, exist_ok=False)
    save_npz(output / "matrix.npz", matrix)
    pd.DataFrame({"itemid": ids}).to_csv(output / "items.csv", index=False)
    manifest = {"kind": "full_training_binary_item_cosine", "cutoff_exclusive_ms": cutoff_ms,
                "top_k": top_k, "block_size": block_size, **counts,
                "nonzeros": matrix.nnz, "train_sha256": fingerprint(train_path),
                "source_sha256": fingerprint(__file__), "user_sampling": None,
                "weighting": "binary distinct user-item incidence; repeats and event type do not increase cosine weight",
                "tie_break": "ascending item ID", "self_similarity": "removed",
                "artifacts_sha256": {n: fingerprint(output / n) for n in ["matrix.npz", "items.csv"]}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--cutoff-ms", type=int, required=True)
    p.add_argument("--top-k", type=int, default=50)
    p.add_argument("--block-size", type=int, default=128)
    a = p.parse_args()
    print(json.dumps(train(a.train, a.output, a.cutoff_ms, a.top_k, a.block_size), indent=2))

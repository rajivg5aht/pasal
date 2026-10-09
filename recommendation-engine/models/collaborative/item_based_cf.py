
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, save_npz


# --------------------------------------------------
# PASAL ITEM-BASED COLLABORATIVE FILTERING
# Sample model for development and testing
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]

TRAIN_PATH = ROOT / "data" / "splits" / "train.csv"
OUTPUT_DIR = ROOT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "item_cf_similarities_sample.npz"
ITEM_IDS_PATH = OUTPUT_DIR / "item_cf_item_ids_sample.csv"

EVENT_WEIGHTS = {
    "view": 1.0,
    "addtocart": 3.0,
    "transaction": 5.0,
}

MAX_USERS = 20_000
MIN_ITEMS_PER_USER = 3
TOP_K = 50


def main():
    print("=== PASAL ITEM-BASED COLLABORATIVE FILTERING ===")

    # 1. Load training data only
    print("\nLoading training interactions...")

    events = pd.read_csv(
        TRAIN_PATH,
        usecols=["visitorid", "itemid", "event"],
    )

    print(f"Training interactions loaded: {len(events):,}")

    events["weight"] = events["event"].map(EVENT_WEIGHTS)
    events = events.dropna(subset=["weight"])

    # 2. Select users with enough interaction history
    print("\nSelecting eligible users...")

    items_per_user = events.groupby("visitorid")["itemid"].nunique()

    eligible_users = items_per_user[
        items_per_user >= MIN_ITEMS_PER_USER
    ].index

    if len(eligible_users) == 0:
        print("No users meet the minimum interaction requirement.")
        return

    rng = np.random.default_rng(42)

    sample_size = min(MAX_USERS, len(eligible_users))

    sampled_users = rng.choice(
        eligible_users.to_numpy(),
        size=sample_size,
        replace=False,
    )

    events = events[events["visitorid"].isin(sampled_users)].copy()

    print(f"Eligible users: {len(eligible_users):,}")
    print(f"Selected users: {len(sampled_users):,}")

    # 3. Aggregate repeated interactions for each user-item pair
    interactions = (
        events.groupby(["visitorid", "itemid"], as_index=False)
        ["weight"]
        .sum()
    )

    print(f"Unique user-item pairs: {len(interactions):,}")

    # 4. Build a sparse binary user-item matrix
    user_codes, user_ids = pd.factorize(interactions["visitorid"])
    item_codes, item_ids = pd.factorize(interactions["itemid"])

    user_item = coo_matrix(
        (
            np.ones(len(interactions), dtype=np.float32),
            (user_codes, item_codes),
        ),
        shape=(len(user_ids), len(item_ids)),
        dtype=np.float32,
    ).tocsr()

    print(f"Users in matrix: {len(user_ids):,}")
    print(f"Items in matrix: {len(item_ids):,}")
    print(f"Non-zero interactions: {user_item.nnz:,}")

    # 5. Calculate item co-occurrence
    # Each value counts users who interacted with both items.
    print("\nCalculating sparse item co-occurrence...")

    cooccurrence = (user_item.T @ user_item).tocsr()
    cooccurrence.setdiag(0)
    cooccurrence.eliminate_zeros()

    print(f"Non-zero co-occurrences: {cooccurrence.nnz:,}")

    # 6. Calculate cosine similarity
    print("\nCalculating cosine similarities...")

    item_norms = np.sqrt(
        np.asarray(user_item.power(2).sum(axis=0)).ravel()
    )

    inverse_norms = np.zeros_like(item_norms, dtype=np.float32)

    nonzero = item_norms > 0
    inverse_norms[nonzero] = 1.0 / item_norms[nonzero]

    similarity = cooccurrence.multiply(inverse_norms[:, None])
    similarity = similarity.multiply(inverse_norms[None, :]).tocsr()

    similarity.setdiag(0)
    similarity.eliminate_zeros()

    print(f"Non-zero similarities before pruning: {similarity.nnz:,}")

    # 7. Keep only the strongest TOP_K neighbors per item
    print(f"\nKeeping at most {TOP_K} neighbors per item...")

    rows = []
    cols = []
    values = []

    for item_index in range(similarity.shape[0]):
        start = similarity.indptr[item_index]
        end = similarity.indptr[item_index + 1]

        neighbor_indices = similarity.indices[start:end]
        neighbor_scores = similarity.data[start:end]

        if len(neighbor_scores) > TOP_K:
            selected = np.argpartition(
                neighbor_scores, -TOP_K
            )[-TOP_K:]

            neighbor_indices = neighbor_indices[selected]
            neighbor_scores = neighbor_scores[selected]

        rows.extend([item_index] * len(neighbor_scores))
        cols.extend(neighbor_indices.tolist())
        values.extend(neighbor_scores.tolist())

    pruned_similarity = coo_matrix(
        (
            np.asarray(values, dtype=np.float32),
            (rows, cols),
        ),
        shape=similarity.shape,
        dtype=np.float32,
    ).tocsr()

    print(f"Non-zero similarities after pruning: {pruned_similarity.nnz:,}")

    # 8. Save model and item ID mapping
    print("\nSaving sample model files...")

    save_npz(OUTPUT_PATH, pruned_similarity)

    pd.DataFrame({"itemid": item_ids}).to_csv(
        ITEM_IDS_PATH,
        index=False,
    )

    print(f"Similarity matrix saved: {OUTPUT_PATH}")
    print(f"Item ID mapping saved: {ITEM_IDS_PATH}")
    print("\nSample collaborative filtering model built successfully.")
    print("Note: This is a development sample, not the final evaluation model.")


if __name__ == "__main__":
    main()
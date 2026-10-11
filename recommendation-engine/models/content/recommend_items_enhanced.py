
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.sparse import load_npz

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_utils import build_user_histories, top_positive_indices


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

TRAIN_FILE = DATA_DIR / "splits" / "train.csv"
MATRIX_FILE = PROCESSED_DIR / "item_tfidf_matrix_enhanced.npz"
ITEM_IDS_FILE = PROCESSED_DIR / "item_tfidf_ids_enhanced.csv"
OUTPUT_FILE = PROCESSED_DIR / "content_recommendations_enhanced.csv"

TOP_K = 10
MAX_HISTORY_ITEMS = 20
MAX_TEST_USERS = 100


def main():
    print("=== PASAL ENHANCED CONTENT-BASED RECOMMENDATIONS ===")

    # 1. Load enhanced TF-IDF artifacts.
    print("\nLoading enhanced TF-IDF matrix...")
    item_matrix = load_npz(MATRIX_FILE).tocsr()
    item_ids = pd.read_csv(ITEM_IDS_FILE)["itemid"].tolist()

    if item_matrix.shape[0] != len(item_ids):
        raise ValueError("TF-IDF matrix rows do not match item IDs.")

    item_to_index = {
        int(item_id): index
        for index, item_id in enumerate(item_ids)
    }

    # 2. Load training interactions.
    print("\nLoading training interactions...")
    train = pd.read_csv(
        TRAIN_FILE,
        usecols=["timestamp", "visitorid", "itemid"],
    ).dropna(subset=["visitorid", "itemid"])

    train["visitorid"] = train["visitorid"].astype("int64")
    train["itemid"] = train["itemid"].astype("int64")

    histories, seen_by_user = build_user_histories(train, MAX_HISTORY_ITEMS)
    user_histories = pd.Series(histories)

    eligible_users = user_histories[
        user_histories.apply(
            lambda history: any(item in item_to_index for item in history)
        )
    ]

    sample_users = eligible_users.head(MAX_TEST_USERS)

    print(f"Users selected: {len(sample_users):,}")
    print("\nGenerating recommendations...")

    results = []

    for count, (user_id, history) in enumerate(
        sample_users.items(),
        start=1,
    ):
        history_indices = [
            item_to_index[item]
            for item in history
            if item in item_to_index
        ]

        if not history_indices:
            continue

        # Create a user profile from historical item vectors.
        profile = item_matrix[history_indices].mean(axis=0).A1

        # Score all items by similarity to the user profile.
        scores = item_matrix.dot(profile).ravel()

        # Exclude items already seen in training.
        seen_indices = [
            item_to_index[item]
            for item in seen_by_user.get(user_id, set())
            if item in item_to_index
        ]
        scores[seen_indices] = -1.0

        # Select the highest-scoring unseen items.
        candidate_indices = top_positive_indices(scores, item_ids, TOP_K)

        rank = 0
        for index in candidate_indices:
            if scores[index] <= 0:
                continue

            rank += 1
            results.append({
                "visitorid": int(user_id),
                "rank": rank,
                "itemid": int(item_ids[index]),
                "similarity_score": float(scores[index]),
            })

        if count % 20 == 0:
            print(f"Processed {count}/{len(sample_users)} users...")

    # 3. Save results separately from the original model.
    columns = [
        "visitorid",
        "rank",
        "itemid",
        "similarity_score",
    ]

    recommendations = pd.DataFrame(results, columns=columns)
    recommendations.to_csv(OUTPUT_FILE, index=False)

    print("\n=== ENHANCED RECOMMENDATION SUMMARY ===")
    print(f"Users selected: {len(sample_users):,}")
    print(
        "Users receiving recommendations: "
        f"{recommendations['visitorid'].nunique() if not recommendations.empty else 0:,}"
    )
    print(f"Recommendations generated: {len(recommendations):,}")
    print(f"Output file: {OUTPUT_FILE}")

    if not recommendations.empty:
        print("\nSample recommendations:")
        print(recommendations.head(10).to_string(index=False))

    print("\nEnhanced recommendation smoke test complete.")


if __name__ == "__main__":
    main()

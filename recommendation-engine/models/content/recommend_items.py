
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.sparse import load_npz

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_utils import build_user_histories, top_positive_indices


DATA_DIR = Path(__file__).resolve().parents[3] / "data"
PROCESSED_DIR = DATA_DIR / "processed"

TRAIN_FILE = DATA_DIR / "splits" / "train.csv"
MATRIX_FILE = PROCESSED_DIR / "item_tfidf_matrix.npz"
ITEM_IDS_FILE = PROCESSED_DIR / "item_tfidf_ids.csv"
OUTPUT_FILE = PROCESSED_DIR / "content_recommendations.csv"

TOP_K = 10
MAX_HISTORY_ITEMS = 20
MAX_TEST_USERS = 100


def main():
    print("=== PASAL CONTENT-BASED RECOMMENDATIONS ===")

    # 1. Load the item feature matrix and item IDs.
    print("Loading TF-IDF matrix...")
    item_matrix = load_npz(MATRIX_FILE).tocsr()
    item_ids = pd.read_csv(ITEM_IDS_FILE)["itemid"].tolist()

    if item_matrix.shape[0] != len(item_ids):
        raise ValueError("TF-IDF matrix rows do not match item IDs.")

    item_to_index = {
        item_id: index for index, item_id in enumerate(item_ids)
    }

    # 2. Load training interactions.
    print("Loading training interactions...")
    train = pd.read_csv(
        TRAIN_FILE,
        usecols=["timestamp", "visitorid", "itemid"]
    ).dropna(subset=["visitorid", "itemid"])

    # Keep each user's most recent unique training items.
    histories, seen_by_user = build_user_histories(train, MAX_HISTORY_ITEMS)
    user_histories = pd.Series(histories)

    # Use a small smoke-test sample for now.
    eligible_users = user_histories[
        user_histories.apply(
            lambda history: any(item in item_to_index for item in history)
        )
    ]
    sample_users = eligible_users.head(MAX_TEST_USERS)

    print(f"Generating recommendations for {len(sample_users)} users...")

    results = []

    # 3. Build a user profile and score every item correctly.
    for count, (user_id, history) in enumerate(sample_users.items(), start=1):
        history_indices = [
            item_to_index[item]
            for item in history
            if item in item_to_index
        ]

        if not history_indices:
            continue

        # Average the user's historical item vectors.
        profile = item_matrix[history_indices].mean(axis=0).A1

        # TF-IDF item rows are L2-normalized, so the dot product
        # provides a cosine-similarity-style score for the profile.
        scores = item_matrix.dot(profile).ravel()

        # Exclude all items the user interacted with during training.
        seen_items = seen_by_user.get(user_id, set())

        seen_indices = [
            item_to_index[item]
            for item in seen_items
            if item in item_to_index
        ]
        scores[seen_indices] = -1.0

        # Rank items by their similarity scores.
        candidate_indices = top_positive_indices(scores, item_ids, TOP_K)

        for rank, index in enumerate(candidate_indices, start=1):
            if scores[index] <= 0:
                continue

            results.append({
                "visitorid": user_id,
                "rank": rank,
                "itemid": item_ids[index],
                "similarity_score": float(scores[index]),
            })

        if count % 20 == 0:
            print(f"Processed {count}/{len(sample_users)} users...")

    # 4. Save recommendations.
    recommendations = pd.DataFrame(
        results,
        columns=[
            "visitorid",
            "rank",
            "itemid",
            "similarity_score"
        ]
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    recommendations.to_csv(OUTPUT_FILE, index=False)

    print("\n=== RECOMMENDATION SUMMARY ===")
    print(f"Users processed: {len(sample_users):,}")
    print(f"Users receiving recommendations: {recommendations['visitorid'].nunique() if not recommendations.empty else 0:,}")
    print(f"Recommendations generated: {len(recommendations):,}")
    print(f"Output file: {OUTPUT_FILE}")

    if not recommendations.empty:
        print("\nSample recommendations:")
        print(recommendations.head(10).to_string(index=False))

    print("\nContent recommendation smoke test complete.")


if __name__ == "__main__":
    main()


from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import load_npz


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "processed"
TRAIN_PATH = ROOT / "data" / "splits" / "train.csv"

SIMILARITY_PATH = DATA_DIR / "item_cf_similarities_sample.npz"
ITEM_IDS_PATH = DATA_DIR / "item_cf_item_ids_sample.csv"

TOP_N = 10


def main():
    print("=== PASAL COLLABORATIVE FILTERING RECOMMENDATIONS ===")

    similarity = load_npz(SIMILARITY_PATH).tocsr()
    item_ids = pd.read_csv(ITEM_IDS_PATH)["itemid"].to_numpy()

    events = pd.read_csv(
        TRAIN_PATH,
        usecols=["visitorid", "itemid"],
    )

    # Select a user who has items represented in our sample model.
    item_to_index = {
        int(item_id): index
        for index, item_id in enumerate(item_ids)
    }

    represented_items = set(item_to_index)
    events = events[events["itemid"].isin(represented_items)]

    user_item_history = (
        events.groupby("visitorid")["itemid"]
        .apply(lambda items: list(dict.fromkeys(items)))
    )

    eligible_users = user_item_history[
        user_item_history.apply(
            lambda items: any(item in represented_items for item in items)
        )
    ]

    if eligible_users.empty:
        print("No eligible users found.")
        return

    visitor_id = eligible_users.index[0]
    history = eligible_users.loc[visitor_id]

    scores = np.zeros(len(item_ids), dtype=np.float32)

    for item_id in history:
        item_index = item_to_index.get(int(item_id))
        if item_index is None:
            continue

        start = similarity.indptr[item_index]
        end = similarity.indptr[item_index + 1]

        neighbor_indices = similarity.indices[start:end]
        neighbor_scores = similarity.data[start:end]

        scores[neighbor_indices] += neighbor_scores

    # Never recommend items already present in the user's history.
    for item_id in history:
        item_index = item_to_index.get(int(item_id))
        if item_index is not None:
            scores[item_index] = -np.inf

    count = min(TOP_N, int(np.isfinite(scores).sum()))
    if count == 0:
        print("No unseen recommendations available.")
        return

    top_indices = np.argsort(scores)[::-1]
    top_indices = [
        index for index in top_indices
        if np.isfinite(scores[index]) and scores[index] > 0
    ][:count]

    recommendations = pd.DataFrame({
        "rank": range(1, len(top_indices) + 1),
        "itemid": item_ids[top_indices],
        "score": scores[top_indices],
    })

    print(f"Sample user ID: {visitor_id}")
    print(f"Items in user's training history: {len(history)}")
    print("\nTop recommendations:")
    print(recommendations.to_string(index=False))

    output_path = DATA_DIR / "item_cf_sample_recommendations.csv"
    recommendations.to_csv(output_path, index=False)
    print(f"\nSaved recommendations: {output_path}")


if __name__ == "__main__":
    main()
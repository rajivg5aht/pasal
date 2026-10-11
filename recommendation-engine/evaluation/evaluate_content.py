
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.sparse import load_npz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_utils import build_user_histories, top_positive_indices


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PROCESSED_DIR = DATA_DIR / "processed"

TRAIN_FILE = DATA_DIR / "splits" / "train.csv"
VALIDATION_FILE = DATA_DIR / "splits" / "validation.csv"
RANKING_FILE = PROCESSED_DIR / "popularity_ranking.csv"
MATRIX_FILE = PROCESSED_DIR / "item_tfidf_matrix.npz"
ITEM_IDS_FILE = PROCESSED_DIR / "item_tfidf_ids.csv"

METRICS_FILE = PROCESSED_DIR / "content_validation_metrics.csv"
DETAILS_FILE = PROCESSED_DIR / "content_validation_recommendations.csv"

K = 10
MAX_USERS = 500
RANDOM_STATE = 42


def calculate_metrics(recommendations, relevant_items):
    hits = [
        1 if item in relevant_items else 0
        for item in recommendations
    ]

    precision = sum(hits) / K
    recall = sum(hits) / len(relevant_items)

    dcg = sum(
        hit / math.log2(position + 2)
        for position, hit in enumerate(hits)
    )

    ideal_hits = min(len(relevant_items), K)
    idcg = sum(
        1 / math.log2(position + 2)
        for position in range(ideal_hits)
    )

    ndcg = dcg / idcg if idcg else 0.0

    return precision, recall, ndcg


def main():
    print("=== PASAL CONTENT MODEL EVALUATION ===")

    # 1. Load item vectors and their matching IDs.
    print("Loading TF-IDF model...")
    item_matrix = load_npz(MATRIX_FILE).tocsr()
    item_ids = pd.read_csv(ITEM_IDS_FILE)["itemid"].tolist()

    if item_matrix.shape[0] != len(item_ids):
        raise ValueError("TF-IDF matrix and item ID mapping do not match.")

    item_to_index = {
        item_id: index
        for index, item_id in enumerate(item_ids)
    }

    # 2. Load training interactions.
    print("Loading training data...")
    train = pd.read_csv(
        TRAIN_FILE,
        usecols=["timestamp", "visitorid", "itemid"]
    ).dropna(subset=["visitorid", "itemid"])

    histories, seen_by_user = build_user_histories(train, 20)

    # 3. Load validation interactions and remove training-seen items
    # from the relevant set.
    print("Loading validation data...")
    validation = pd.read_csv(
        VALIDATION_FILE,
        usecols=["visitorid", "itemid"]
    ).dropna(subset=["visitorid", "itemid"])

    relevant_by_user = {}

    for user_id, group in validation.groupby("visitorid"):
        seen = seen_by_user.get(user_id, set())
        relevant = set(group["itemid"]) - seen

        if relevant and any(
            item in item_to_index
            for item in histories.get(user_id, [])
        ):
            relevant_by_user[user_id] = relevant

    if not relevant_by_user:
        print("No eligible validation users were found.")
        return

    # Select a reproducible sample of eligible users.
    eligible_ids = list(relevant_by_user.keys())
    sample_size = min(MAX_USERS, len(eligible_ids))

    rng = np.random.default_rng(RANDOM_STATE)
    sampled_users = rng.choice(
        eligible_ids,
        size=sample_size,
        replace=False
    )

    print(f"Users selected for evaluation: {sample_size:,}")

    # 4. Load the popularity baseline for a fair comparison.
    popularity = pd.read_csv(RANKING_FILE)
    ranked_items = popularity["itemid"].tolist()

    results = []
    detail_rows = []

    content_precisions = []
    content_recalls = []
    content_ndcgs = []

    popularity_precisions = []
    popularity_recalls = []
    popularity_ndcgs = []

    content_recommended_items = set()
    popularity_recommended_items = set()

    # 5. Evaluate both methods for the same users.
    for count, user_id in enumerate(sampled_users, start=1):
        seen = seen_by_user.get(user_id, set())
        relevant = relevant_by_user[user_id]

        # Popularity recommendations: exclude training-seen items.
        popularity_recs = []

        for item in ranked_items:
            if item not in seen:
                popularity_recs.append(item)

                if len(popularity_recs) == K:
                    break

        # Content-based recommendations from the user's history.
        history = histories.get(user_id, [])

        history_indices = [
            item_to_index[item]
            for item in history
            if item in item_to_index
        ]

        content_recs = []

        if history_indices:
            profile = item_matrix[history_indices].mean(axis=0).A1
            scores = item_matrix.dot(profile).ravel()

            seen_indices = [
                item_to_index[item]
                for item in seen
                if item in item_to_index
            ]

            scores[seen_indices] = -np.inf

            # Find the highest-scoring candidates efficiently.
            candidate_indices = top_positive_indices(scores, item_ids, K)

            for index in candidate_indices:
                if scores[index] <= 0:
                    continue

                content_recs.append(item_ids[index])

                if len(content_recs) == K:
                    break

        # Calculate metrics against the same relevant items.
        cp, cr, cn = calculate_metrics(content_recs, relevant)
        pp, pr, pn = calculate_metrics(popularity_recs, relevant)

        content_precisions.append(cp)
        content_recalls.append(cr)
        content_ndcgs.append(cn)

        popularity_precisions.append(pp)
        popularity_recalls.append(pr)
        popularity_ndcgs.append(pn)

        content_recommended_items.update(content_recs)
        popularity_recommended_items.update(popularity_recs)

        for rank, item in enumerate(content_recs, start=1):
            detail_rows.append({
                "visitorid": user_id,
                "model": "content",
                "rank": rank,
                "itemid": item,
                "relevant": item in relevant,
            })

        for rank, item in enumerate(popularity_recs, start=1):
            detail_rows.append({
                "visitorid": user_id,
                "model": "popularity",
                "rank": rank,
                "itemid": item,
                "relevant": item in relevant,
            })

        if count % 100 == 0:
            print(f"Evaluated {count}/{sample_size} users...")

    # 6. Summarize the metrics.
    results = [
        {
            "model": "content",
            "k": K,
            "users_evaluated": sample_size,
            "precision_at_10": np.mean(content_precisions),
            "mean_recall_at_10": np.mean(content_recalls),
            "ndcg_at_10": np.mean(content_ndcgs),
            "unique_items_recommended": len(content_recommended_items),
        },
        {
            "model": "popularity",
            "k": K,
            "users_evaluated": sample_size,
            "precision_at_10": np.mean(popularity_precisions),
            "mean_recall_at_10": np.mean(popularity_recalls),
            "ndcg_at_10": np.mean(popularity_ndcgs),
            "unique_items_recommended": len(popularity_recommended_items),
        },
    ]

    metrics = pd.DataFrame(results)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(METRICS_FILE, index=False)
    pd.DataFrame(detail_rows).to_csv(DETAILS_FILE, index=False)

    print("\n=== VALIDATION RESULTS ===")
    print(metrics.to_string(index=False))
    print(f"\nMetrics saved to: {METRICS_FILE}")
    print(f"Recommendation details saved to: {DETAILS_FILE}")
    print("Evaluation complete.")


if __name__ == "__main__":
    main()

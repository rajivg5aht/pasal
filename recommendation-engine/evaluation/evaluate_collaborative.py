
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import load_npz


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
SPLIT_DIR = ROOT / "data" / "splits"

TRAIN_PATH = SPLIT_DIR / "train.csv"
VALIDATION_PATH = SPLIT_DIR / "validation.csv"

SIMILARITY_PATH = DATA_DIR / "item_cf_similarities_sample.npz"
ITEM_IDS_PATH = DATA_DIR / "item_cf_item_ids_sample.csv"

METRICS_PATH = DATA_DIR / "collaborative_validation_metrics.csv"
DETAILS_PATH = DATA_DIR / "collaborative_validation_recommendations.csv"

K = 10
MAX_USERS = 500
RANDOM_SEED = 42


def precision_at_k(recommended, relevant, k):
    return len(set(recommended[:k]) & relevant) / k


def recall_at_k(recommended, relevant, k):
    if not relevant:
        return 0.0
    return len(set(recommended[:k]) & relevant) / len(relevant)


def ndcg_at_k(recommended, relevant, k):
    dcg = sum(
        1.0 / np.log2(rank + 2)
        for rank, item in enumerate(recommended[:k])
        if item in relevant
    )

    ideal_hits = min(len(relevant), k)
    idcg = sum(
        1.0 / np.log2(rank + 2)
        for rank in range(ideal_hits)
    )

    return dcg / idcg if idcg else 0.0


def recommend_items(user_history, similarity, item_to_index, item_ids, k=10):
    scores = {}

    for item_id in user_history:
        item_index = item_to_index.get(int(item_id))

        if item_index is None:
            continue

        start = similarity.indptr[item_index]
        end = similarity.indptr[item_index + 1]

        neighbors = similarity.indices[start:end]
        similarities = similarity.data[start:end]

        for neighbor_index, score in zip(neighbors, similarities):
            candidate_id = int(item_ids[neighbor_index])

            if candidate_id in user_history:
                continue

            scores[candidate_id] = scores.get(candidate_id, 0.0) + float(score)

    ranked = sorted(
        scores.items(),
        key=lambda pair: (-pair[1], pair[0]),
    )

    return ranked[:k]


def main():
    print("=== PASAL COLLABORATIVE FILTERING EVALUATION ===")

    print("\nLoading similarity model...")
    similarity = load_npz(SIMILARITY_PATH).tocsr()
    item_ids = pd.read_csv(ITEM_IDS_PATH)["itemid"].to_numpy()

    item_to_index = {
        int(item_id): index
        for index, item_id in enumerate(item_ids)
    }

    print("\nLoading training interactions...")
    train = pd.read_csv(
        TRAIN_PATH,
        usecols=["visitorid", "itemid"],
    )

    train_history = (
        train.groupby("visitorid")["itemid"]
        .apply(lambda items: set(items.astype(int)))
        .to_dict()
    )

    print("\nLoading validation interactions...")
    validation = pd.read_csv(
        VALIDATION_PATH,
        usecols=["visitorid", "itemid"],
    )

    validation_relevant = (
        validation.groupby("visitorid")["itemid"]
        .apply(lambda items: set(items.astype(int)))
        .to_dict()
    )

    # Evaluate users with at least one relevant item and
    # at least one training item covered by this model.
    eligible = []

    for user_id, relevant_items in validation_relevant.items():
        history = train_history.get(user_id, set())

        unseen_relevant = relevant_items - history
        has_covered_history = any(
            item_id in item_to_index for item_id in history
        )

        if unseen_relevant and has_covered_history:
            eligible.append(user_id)

    if not eligible:
        print("No eligible validation users found.")
        return

    rng = np.random.default_rng(RANDOM_SEED)
    selected_users = rng.choice(
        eligible,
        size=min(MAX_USERS, len(eligible)),
        replace=False,
    )

    print(f"Eligible users: {len(eligible):,}")
    print(f"Users selected: {len(selected_users):,}")

    metric_rows = []
    recommendation_rows = []

    for count, user_id in enumerate(selected_users, start=1):
        history = train_history.get(user_id, set())
        relevant = validation_relevant.get(user_id, set()) - history

        ranked = recommend_items(
            history,
            similarity,
            item_to_index,
            item_ids,
            K,
        )

        recommended_ids = [item_id for item_id, _ in ranked]

        metric_rows.append({
            "visitorid": int(user_id),
            "precision_at_10": precision_at_k(recommended_ids, relevant, K),
            "recall_at_10": recall_at_k(recommended_ids, relevant, K),
            "ndcg_at_10": ndcg_at_k(recommended_ids, relevant, K),
            "recommendations_count": len(recommended_ids),
        })

        for rank, (item_id, score) in enumerate(ranked, start=1):
            recommendation_rows.append({
                "visitorid": int(user_id),
                "rank": rank,
                "itemid": item_id,
                "score": score,
                "relevant": item_id in relevant,
            })

        if count % 100 == 0:
            print(f"Evaluated {count}/{len(selected_users)} users...")

    metrics = pd.DataFrame(metric_rows)
    recommendations = pd.DataFrame(recommendation_rows)

    summary = pd.DataFrame([{
        "model": "collaborative_sample",
        "k": K,
        "users_evaluated": len(metrics),
        "precision_at_10": metrics["precision_at_10"].mean(),
        "mean_recall_at_10": metrics["recall_at_10"].mean(),
        "ndcg_at_10": metrics["ndcg_at_10"].mean(),
        "unique_items_recommended": (
            recommendations["itemid"].nunique()
            if not recommendations.empty else 0
        ),
        "users_with_recommendations": int(
            (metrics["recommendations_count"] > 0).sum()
        ),
    }])

    summary.to_csv(METRICS_PATH, index=False)
    recommendations.to_csv(DETAILS_PATH, index=False)

    print("\n=== COLLABORATIVE FILTERING RESULTS ===")
    print(summary.to_string(index=False))

    print(f"\nMetrics saved: {METRICS_PATH}")
    print(f"Recommendation details saved: {DETAILS_PATH}")


if __name__ == "__main__":
    main()
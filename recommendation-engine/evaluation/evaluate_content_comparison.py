
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import load_npz


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

TRAIN_FILE = DATA_DIR / "splits" / "train.csv"
VALIDATION_FILE = DATA_DIR / "splits" / "validation.csv"
RANKING_FILE = PROCESSED_DIR / "popularity_ranking.csv"

ORIGINAL_MATRIX_FILE = PROCESSED_DIR / "item_tfidf_matrix.npz"
ORIGINAL_IDS_FILE = PROCESSED_DIR / "item_tfidf_ids.csv"

ENHANCED_MATRIX_FILE = PROCESSED_DIR / "item_tfidf_matrix_enhanced.npz"
ENHANCED_IDS_FILE = PROCESSED_DIR / "item_tfidf_ids_enhanced.csv"

METRICS_FILE = PROCESSED_DIR / "content_model_comparison_metrics.csv"
DETAILS_FILE = PROCESSED_DIR / "content_model_comparison_details.csv"

K = 10
MAX_USERS = 100
RANDOM_STATE = 42
MAX_HISTORY_ITEMS = 20


def calculate_metrics(recommendations, relevant_items):
    hits = [
        1 if item in relevant_items else 0
        for item in recommendations
    ]

    precision = sum(hits) / K
    recall = (
        sum(hits) / len(relevant_items)
        if relevant_items
        else 0.0
    )

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


def load_content_model(matrix_file, ids_file, model_name):
    print(f"Loading {model_name} model...")

    matrix = load_npz(matrix_file).tocsr()
    item_ids = pd.read_csv(ids_file)["itemid"].astype("int64").tolist()

    if matrix.shape[0] != len(item_ids):
        raise ValueError(
            f"{model_name}: matrix rows do not match item IDs."
        )

    item_to_index = {
        item_id: index
        for index, item_id in enumerate(item_ids)
    }

    print(
        f"{model_name}: {len(item_ids):,} items, "
        f"{matrix.shape[1]:,} TF-IDF features"
    )

    return matrix, item_ids, item_to_index


def recommend_content(
    user_id,
    history,
    seen_items,
    matrix,
    item_ids,
    item_to_index,
):
    history_indices = [
        item_to_index[item]
        for item in history
        if item in item_to_index
    ]

    if not history_indices:
        return []

    # Build a profile from the user's training history.
    profile = matrix[history_indices].mean(axis=0).A1

    # Score all items against the profile.
    scores = matrix.dot(profile).ravel()

    # Never recommend items already seen in training.
    seen_indices = [
        item_to_index[item]
        for item in seen_items
        if item in item_to_index
    ]
    scores[seen_indices] = -np.inf

    candidate_count = min(K, len(scores))
    candidate_indices = np.argpartition(
        scores, -candidate_count
    )[-candidate_count:]

    candidate_indices = candidate_indices[
        np.argsort(scores[candidate_indices])[::-1]
    ]

    recommendations = []

    for index in candidate_indices:
        if scores[index] <= 0:
            continue

        recommendations.append(int(item_ids[index]))

        if len(recommendations) == K:
            break

    return recommendations


def recommend_popularity(ranked_items, seen_items):
    recommendations = []

    for item_id in ranked_items:
        if item_id not in seen_items:
            recommendations.append(item_id)

            if len(recommendations) == K:
                break

    return recommendations


def main():
    print("=== PASAL CONTENT MODEL COMPARISON ===")

    # 1. Load both content models.
    original_matrix, original_ids, original_map = load_content_model(
        ORIGINAL_MATRIX_FILE,
        ORIGINAL_IDS_FILE,
        "Original content",
    )

    enhanced_matrix, enhanced_ids, enhanced_map = load_content_model(
        ENHANCED_MATRIX_FILE,
        ENHANCED_IDS_FILE,
        "Enhanced content",
    )

    # 2. Load popularity ranking.
    print("\nLoading popularity ranking...")
    popularity_df = pd.read_csv(RANKING_FILE)
    ranked_items = (
        popularity_df["itemid"].dropna().astype("int64").tolist()
    )

    # Use a shared catalog denominator for coverage.
    shared_catalog = (
        set(original_ids)
        | set(enhanced_ids)
        | set(ranked_items)
    )
    catalog_size = len(shared_catalog)

    # 3. Load training data and construct histories.
    print("Loading training interactions...")
    train = pd.read_csv(
        TRAIN_FILE,
        usecols=["visitorid", "itemid"],
    ).dropna(subset=["visitorid", "itemid"])

    train["visitorid"] = train["visitorid"].astype("int64")
    train["itemid"] = train["itemid"].astype("int64")

    seen_by_user = (
        train.groupby("visitorid", sort=False)["itemid"]
        .apply(set)
        .to_dict()
    )

    histories = (
        train.groupby("visitorid", sort=False)["itemid"]
        .apply(
            lambda values: list(
                dict.fromkeys(values)
            )[-MAX_HISTORY_ITEMS:]
        )
        .to_dict()
    )

    # 4. Identify users with relevant validation items and usable
    # histories in BOTH content models.
    print("Loading validation interactions...")
    validation = pd.read_csv(
        VALIDATION_FILE,
        usecols=["visitorid", "itemid"],
    ).dropna(subset=["visitorid", "itemid"])

    validation["visitorid"] = validation["visitorid"].astype("int64")
    validation["itemid"] = validation["itemid"].astype("int64")

    relevant_by_user = {}

    for user_id, group in validation.groupby("visitorid"):
        seen = seen_by_user.get(user_id, set())
        relevant = set(group["itemid"]) - seen
        history = histories.get(user_id, [])

        has_original_history = any(
            item in original_map for item in history
        )
        has_enhanced_history = any(
            item in enhanced_map for item in history
        )

        if (
            relevant
            and has_original_history
            and has_enhanced_history
        ):
            relevant_by_user[user_id] = relevant

    if not relevant_by_user:
        raise ValueError("No eligible validation users were found.")

    # 5. Select one reproducible sample for all three models.
    eligible_ids = np.array(list(relevant_by_user.keys()))
    sample_size = min(MAX_USERS, len(eligible_ids))

    rng = np.random.default_rng(RANDOM_STATE)
    sampled_users = rng.choice(
        eligible_ids,
        size=sample_size,
        replace=False,
    )

    print(f"\nShared validation users: {sample_size:,}")
    print(f"Catalog size for coverage: {catalog_size:,}")
    print("\nEvaluating all three models...")

    model_names = [
        "popularity",
        "content_original",
        "content_enhanced",
    ]

    metric_values = {
        name: {"precision": [], "recall": [], "ndcg": []}
        for name in model_names
    }
    recommended_items = {name: set() for name in model_names}
    detail_rows = []

    # 6. Evaluate each model on exactly the same users.
    for count, user_id in enumerate(sampled_users, start=1):
        user_id = int(user_id)
        seen = seen_by_user.get(user_id, set())
        relevant = relevant_by_user[user_id]
        history = histories.get(user_id, [])

        recommendations_by_model = {
            "popularity": recommend_popularity(ranked_items, seen),
            "content_original": recommend_content(
                user_id,
                history,
                seen,
                original_matrix,
                original_ids,
                original_map,
            ),
            "content_enhanced": recommend_content(
                user_id,
                history,
                seen,
                enhanced_matrix,
                enhanced_ids,
                enhanced_map,
            ),
        }

        for model_name, recommendations in recommendations_by_model.items():
            precision, recall, ndcg = calculate_metrics(
                recommendations,
                relevant,
            )

            metric_values[model_name]["precision"].append(precision)
            metric_values[model_name]["recall"].append(recall)
            metric_values[model_name]["ndcg"].append(ndcg)
            recommended_items[model_name].update(recommendations)

            for rank, item_id in enumerate(recommendations, start=1):
                detail_rows.append({
                    "visitorid": user_id,
                    "model": model_name,
                    "rank": rank,
                    "itemid": item_id,
                    "relevant": item_id in relevant,
                })

        if count % 20 == 0:
            print(f"Evaluated {count}/{sample_size} users...")

    # 7. Summarize metrics and catalog coverage.
    rows = []

    for model_name in model_names:
        values = metric_values[model_name]
        unique_count = len(recommended_items[model_name])

        rows.append({
            "model": model_name,
            "k": K,
            "users_evaluated": sample_size,
            "precision_at_10": np.mean(values["precision"]),
            "mean_recall_at_10": np.mean(values["recall"]),
            "ndcg_at_10": np.mean(values["ndcg"]),
            "unique_items_recommended": unique_count,
            "catalog_coverage_pct": (
                100 * unique_count / catalog_size
                if catalog_size
                else 0.0
            ),
        })

    metrics = pd.DataFrame(rows)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(METRICS_FILE, index=False)
    pd.DataFrame(detail_rows).to_csv(DETAILS_FILE, index=False)

    print("\n=== COMPARISON RESULTS ===")
    print(metrics.round(6).to_string(index=False))
    print(f"\nMetrics saved to: {METRICS_FILE}")
    print(f"Recommendation details saved to: {DETAILS_FILE}")
    print("\nComparison complete.")


if __name__ == "__main__":
    main()
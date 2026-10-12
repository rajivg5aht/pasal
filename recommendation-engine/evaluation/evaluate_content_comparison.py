
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import load_npz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_utils import (binary_ranking_metrics, build_user_histories,
                            top_positive_indices, validate_matrix_ids)

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

K = 10
MAX_USERS = 100
RANDOM_STATE = 42
MAX_HISTORY_ITEMS = 20


def calculate_metrics(recommendations, relevant_items):
    return binary_ranking_metrics(recommendations, relevant_items, K)


def load_content_model(matrix_file, ids_file, model_name):
    print(f"Loading {model_name} model...")

    matrix = load_npz(matrix_file).tocsr()
    item_ids = pd.read_csv(ids_file)["itemid"].astype("int64").tolist()

    validate_matrix_ids(matrix, item_ids, model_name)

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

    candidate_indices = top_positive_indices(scores, item_ids, K)

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


def main(output_dir, max_users=MAX_USERS):
    # Never overwrite historical research outputs.
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
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
        usecols=["timestamp", "visitorid", "itemid"],
    ).dropna(subset=["visitorid", "itemid"])

    train["visitorid"] = train["visitorid"].astype("int64")
    train["itemid"] = train["itemid"].astype("int64")

    histories, seen_by_user = build_user_histories(train, MAX_HISTORY_ITEMS)
    interaction_counts = train.groupby("visitorid").size().to_dict()

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
    sample_size = min(max_users, len(eligible_ids))

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
    user_rows = []

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
            user_rows.append({
                "visitorid": user_id, "model": model_name,
                "training_interactions": int(interaction_counts.get(user_id, 0)),
                "relevant_items": len(relevant),
                "relevant_items_outside_catalog": len(relevant - shared_catalog),
                "recommendations_count": len(recommendations),
                "precision_at_10": precision, "recall_at_10": recall, "ndcg_at_10": ndcg,
            })

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
            "users_with_recommendations": sum(
                row["recommendations_count"] > 0 for row in user_rows if row["model"] == model_name
            ),
            "catalog_size": catalog_size,
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

    metrics_file = output_dir / "metrics.csv"
    details_file = output_dir / "recommendations.csv"
    metrics.to_csv(metrics_file, index=False)
    pd.DataFrame(detail_rows, columns=["visitorid", "model", "rank", "itemid", "relevant"]).to_csv(details_file, index=False)
    pd.DataFrame(user_rows).to_csv(output_dir / "per_user_metrics.csv", index=False)
    inputs = [TRAIN_FILE, VALIDATION_FILE, RANKING_FILE, ORIGINAL_MATRIX_FILE,
              ORIGINAL_IDS_FILE, ENHANCED_MATRIX_FILE, ENHANCED_IDS_FILE,
              Path(__file__), Path(__file__).resolve().parents[1] / "research_utils.py"]
    hashes = {}
    for path in inputs:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        hashes[str(path.relative_to(ROOT_DIR))] = digest.hexdigest()
    manifest = {
        "status": "development_diagnostic_not_final_thesis_evidence",
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
        "k": K, "seed": RANDOM_STATE, "max_history_items": MAX_HISTORY_ITEMS,
        "eligible_users": len(eligible_ids), "sampled_users": sampled_users.tolist(),
        "user_policy": "unseen validation targets and history covered by BOTH content models; excludes zero-history users",
        "relevance": "all recorded validation event types; unseen training items only",
        "candidate_policy": "each existing model's catalog; union denominator; temporal availability NOT verified",
        "catalog_size": catalog_size, "tie_break": "score descending, itemid ascending",
        "limitations": ["legacy time-duration split", "metadata timestamps lost during preprocessing",
                        "not a cold-start cohort evaluation", "property enhancement is not GenAI"],
        "input_sha256": hashes,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("\n=== COMPARISON RESULTS ===")
    print(metrics.round(6).to_string(index=False))
    print(f"\nMetrics saved to: {metrics_file}")
    print(f"Recommendation details saved to: {details_file}")
    print("Development diagnostic only: see manifest.json for limitations.")
    print("\nComparison complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Development content comparison; preserves existing artifacts")
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory; must not exist")
    parser.add_argument("--max-users", type=int, default=MAX_USERS)
    args = parser.parse_args()
    if args.max_users < 1:
        parser.error("--max-users must be positive")
    main(args.output_dir, args.max_users)

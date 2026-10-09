
import math
import pandas as pd
from pathlib import Path

DATA = Path("data")

RANKING_FILE = DATA / "processed" / "popularity_ranking.csv"
TRAIN_FILE = DATA / "splits" / "train.csv"
VALIDATION_FILE = DATA / "splits" / "validation.csv"
OUTPUT_FILE = DATA / "processed" / "popularity_validation_metrics.csv"

K = 10


def main():
    print("=== PASAL POPULARITY EVALUATION ===")

    # Load the popularity ranking built from training data only.
    print("Loading popularity ranking...")
    ranking = pd.read_csv(RANKING_FILE)
    ranked_items = ranking["itemid"].tolist()

    # Load training interactions and identify items each user has seen.
    print("Loading training interactions...")
    train = pd.read_csv(
        TRAIN_FILE,
        usecols=["visitorid", "itemid"]
    )

    seen_by_user = (
        train.groupby("visitorid")["itemid"]
        .apply(set)
        .to_dict()
    )

    # Load validation interactions.
    print("Loading validation interactions...")
    validation = pd.read_csv(
        VALIDATION_FILE,
        usecols=["visitorid", "itemid"]
    )

    # Evaluate only validation items not seen by that user in training.
    relevant_by_user = {}

    for user_id, group in validation.groupby("visitorid"):
        seen_items = seen_by_user.get(user_id, set())
        relevant_items = set(group["itemid"]) - seen_items

        if relevant_items:
            relevant_by_user[user_id] = relevant_items

    if not relevant_by_user:
        print("No eligible validation users found.")
        return

    precisions = []
    recalls = []
    ndcgs = []

    print(f"Evaluating {len(relevant_by_user):,} users...")

    # Generate recommendations and calculate metrics per user.
    for user_id, relevant_items in relevant_by_user.items():
        seen_items = seen_by_user.get(user_id, set())

        # Stop once K unseen recommendations have been found.
        recommendations = []

        for item in ranked_items:
            if item not in seen_items:
                recommendations.append(item)

                if len(recommendations) == K:
                    break

        # Identify recommended items that are relevant.
        hits = [
            1 if item in relevant_items else 0
            for item in recommendations
        ]

        # Precision uses K as the denominator.
        precisions.append(sum(hits) / K)

        # Recall uses eligible, unseen validation items.
        recalls.append(
            sum(hits) / len(relevant_items)
        )

        # Calculate NDCG@K.
        dcg = sum(
            hit / math.log2(position + 2)
            for position, hit in enumerate(hits)
        )

        ideal_hits = min(len(relevant_items), K)

        idcg = sum(
            1 / math.log2(position + 2)
            for position in range(ideal_hits)
        )

        ndcgs.append(
            dcg / idcg if idcg > 0 else 0.0
        )

    # Summarize the results.
    metrics = pd.DataFrame([{
        "model": "popularity",
        "k": K,
        "users_evaluated": len(relevant_by_user),
        "precision_at_10": sum(precisions) / len(precisions),
        "mean_recall_at_10": sum(recalls) / len(recalls),
        "ndcg_at_10": sum(ndcgs) / len(ndcgs),
    }])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(OUTPUT_FILE, index=False)

    print("\n=== POPULARITY BASELINE RESULTS ===")
    print(metrics.to_string(index=False))
    print(f"\nSaved metrics to: {OUTPUT_FILE}")
    print("Evaluation complete.")


if __name__ == "__main__":
    main()
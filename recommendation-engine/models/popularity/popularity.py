
import pandas as pd
from pathlib import Path

# Project paths
TRAIN_FILE = Path("data/splits/train.csv")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "popularity_ranking.csv"

# Interaction weights
EVENT_WEIGHTS = {
    "view": 1,
    "addtocart": 3,
    "transaction": 5,
}


def main():
    print("=== PASAL POPULARITY RECOMMENDER ===")

    # Load training interactions only
    events = pd.read_csv(
        TRAIN_FILE,
        usecols=["event", "itemid"]
    )

    print(f"Training interactions: {len(events):,}")

    # Assign a weight to each interaction
    events["score"] = events["event"].map(EVENT_WEIGHTS)

    # Calculate each item's weighted popularity
    ranking = (
        events.groupby("itemid")
        .agg(
            interaction_count=("score", "size"),
            popularity_score=("score", "sum"),
        )
        .reset_index()
        .sort_values(
            ["popularity_score", "interaction_count"],
            ascending=False
        )
        .reset_index(drop=True)
    )

    ranking.insert(0, "rank", range(1, len(ranking) + 1))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ranking.to_csv(OUTPUT_FILE, index=False)

    print(f"Unique items ranked: {len(ranking):,}")
    print(f"Saved ranking to: {OUTPUT_FILE}")

    print("\n=== TOP 10 POPULAR ITEMS ===")
    print(ranking.head(10).to_string(index=False))

    print("\nPopularity model complete.")


if __name__ == "__main__":
    main()

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.sparse import load_npz

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from research_utils import select_profile_history, top_positive_indices, validate_matrix_ids

# ============================================================
# 1. PROJECT PATHS AND CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = ROOT / "data" / "processed"
TRAIN_PATH = ROOT / "data" / "splits" / "train.csv"

POPULARITY_PATH = PROCESSED_DIR / "popularity_ranking.csv"

CONTENT_MATRIX_PATH = PROCESSED_DIR / "item_tfidf_matrix.npz"
CONTENT_IDS_PATH = PROCESSED_DIR / "item_tfidf_ids.csv"

CF_MATRIX_PATH = PROCESSED_DIR / "item_cf_similarities_sample.npz"
CF_IDS_PATH = PROCESSED_DIR / "item_cf_item_ids_sample.csv"

OUTPUT_PATH = PROCESSED_DIR / "hybrid_sample_recommendations.csv"

WEIGHTS = {
    "popularity": 0.33,
    "content": 0.34,
    "collaborative": 0.33,
}

EVENT_WEIGHTS = {
    "view": 1.0,
    "addtocart": 3.0,
    "transaction": 5.0,
}

TOP_N = 10
MAX_HISTORY_ITEMS = 20


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def normalize_scores(scores):
    """Normalize non-negative scores using their maximum."""
    scores = np.asarray(scores, dtype=np.float32)

    scores = np.nan_to_num(
        scores,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    scores = np.maximum(scores, 0.0)

    maximum = scores.max() if scores.size else 0.0

    if maximum > 0:
        scores = scores / maximum

    return scores


def print_score_diagnostics(name, scores):
    """Display score statistics to help identify weak signals."""
    scores = np.asarray(scores, dtype=np.float32)

    print(f"\n=== {name} SCORE DIAGNOSTICS ===")

    if scores.size == 0:
        print("No scores available.")
        return

    print(f"Minimum raw score: {scores.min():.6f}")
    print(f"Maximum raw score: {scores.max():.6f}")
    print(f"Mean raw score: {scores.mean():.6f}")
    print(
        "Unique scores (rounded to 6 decimals):",
        pd.Series(scores).round(6).nunique(),
    )

    print("\nMost common raw scores:")

    print(
        pd.Series(scores)
        .round(6)
        .value_counts()
        .head(10)
        .to_string(),
    )


# ============================================================
# 3. MAIN RECOMMENDER
# ============================================================

def main():
    print("=== PASAL FIXED HYBRID RECOMMENDER ===")

    # --------------------------------------------------------
    # Load existing data and model files
    # --------------------------------------------------------

    print("\nLoading training interactions...")

    train = pd.read_csv(
        TRAIN_PATH,
        usecols=["visitorid", "itemid", "event", "timestamp"],
    )

    popularity = pd.read_csv(POPULARITY_PATH)

    content_matrix = load_npz(CONTENT_MATRIX_PATH)
    content_ids = pd.read_csv(CONTENT_IDS_PATH)["itemid"].to_numpy()

    cf_matrix = load_npz(CF_MATRIX_PATH)
    cf_ids = pd.read_csv(CF_IDS_PATH)["itemid"].to_numpy()
    validate_matrix_ids(content_matrix, content_ids)
    validate_matrix_ids(cf_matrix, cf_ids, "collaborative")
    if cf_matrix.shape != (len(cf_ids), len(cf_ids)):
        raise ValueError("Collaborative similarity matrix must be square and match IDs")

    print(f"Training events: {len(train):,}")
    print(f"Content items: {len(content_ids):,}")
    print(f"Collaborative sample items: {len(cf_ids):,}")

    # Validate the item mappings.
    if content_matrix.shape[0] != len(content_ids):
        raise ValueError(
            "Content matrix rows do not match the content item IDs."
        )

    if cf_matrix.shape[0] != len(cf_ids):
        raise ValueError(
            "Collaborative matrix rows do not match its item IDs."
        )

    if not np.isclose(sum(WEIGHTS.values()), 1.0):
        raise ValueError("Hybrid weights must sum to 1.0.")

    # --------------------------------------------------------
    # Build item ID mappings
    # --------------------------------------------------------

    content_index = {
        int(item_id): index
        for index, item_id in enumerate(content_ids)
    }

    cf_index = {
        int(item_id): index
        for index, item_id in enumerate(cf_ids)
    }

    popularity_scores = popularity.set_index("itemid")[
        "popularity_score"
    ].to_dict()

    # Align popularity scores with the content item order.
    popularity_raw = np.array(
        [
            np.log1p(
                max(
                    0.0,
                    float(popularity_scores.get(int(item_id), 0.0)),
                )
            )
            for item_id in content_ids
        ],
        dtype=np.float32,
    )

    popularity_values = normalize_scores(popularity_raw)

    # --------------------------------------------------------
    # Clean and organize training history
    # --------------------------------------------------------

    train = train.dropna(subset=["visitorid", "itemid"]).copy()

    train["visitorid"] = train["visitorid"].astype("int64")
    train["itemid"] = train["itemid"].astype("int64")

    train["event_weight"] = (
        train["event"].map(EVENT_WEIGHTS).fillna(1.0)
    )

    user_history = (
        train.sort_values("timestamp")
        .drop_duplicates(
            subset=["visitorid", "itemid"],
            keep="last",
        )
    )

    # Find a user represented in both recommendation models.
    selected_user = None
    history = None

    for visitor_id, group in user_history.groupby(
        "visitorid",
        sort=False,
    ):
        group = group.sort_values("timestamp", ascending=False)

        history_ids = group["itemid"].astype(int).tolist()

        content_matches = [
            item_id
            for item_id in history_ids
            if item_id in content_index
        ]

        cf_matches = [
            item_id
            for item_id in history_ids
            if item_id in cf_index
        ]

        if len(content_matches) >= 2 and len(cf_matches) >= 1:
            selected_user = int(visitor_id)
            history = group
            break

    if selected_user is None:
        raise RuntimeError(
            "Could not find a user with sufficient model coverage."
        )

    history, seen_items = select_profile_history(history, MAX_HISTORY_ITEMS)

    print(f"\nSelected development user: {selected_user}")
    print(f"Recent history items: {len(history)}")

    # --------------------------------------------------------
    # Calculate content-based scores
    # --------------------------------------------------------

    content_history_rows = [
        content_index[int(item_id)]
        for item_id in history["itemid"]
        if int(item_id) in content_index
    ]

    if not content_history_rows:
        raise RuntimeError(
            "The selected user's history has no content features."
        )

    # Average the feature vectors of the user's recent items.
    profile = content_matrix[content_history_rows].mean(axis=0)
    profile = np.asarray(profile).ravel()

    # These are raw cosine-like similarities from the TF-IDF matrix.
    raw_content_scores = np.asarray(
        content_matrix.dot(profile)
    ).ravel()

    # Print diagnostics BEFORE normalization.
    print_score_diagnostics(
        "CONTENT RAW",
        raw_content_scores,
    )

    content_scores = normalize_scores(raw_content_scores)

    print_score_diagnostics(
        "CONTENT NORMALIZED",
        content_scores,
    )

    # --------------------------------------------------------
    # Calculate collaborative scores
    # --------------------------------------------------------

    cf_history = []

    for row in history.itertuples(index=False):
        item_id = int(row.itemid)

        if item_id in cf_index:
            event_weight = float(row.event_weight)

            cf_history.append(
                (cf_index[item_id], event_weight)
            )

    weighted_cf_scores = np.zeros(
        len(cf_ids),
        dtype=np.float32,
    )

    for item_row, event_weight in cf_history:
        weighted_cf_scores += (
            cf_matrix.getrow(item_row).toarray().ravel()
            * event_weight
        )

    cf_scores_by_item = normalize_scores(weighted_cf_scores)

    # Align collaborative scores with the content item order.
    cf_scores = np.array(
        [
            cf_scores_by_item[cf_index[int(item_id)]]
            if int(item_id) in cf_index
            else 0.0
            for item_id in content_ids
        ],
        dtype=np.float32,
    )

    # --------------------------------------------------------
    # Combine normalized signals
    # --------------------------------------------------------

    hybrid_scores = (
        WEIGHTS["popularity"] * popularity_values
        + WEIGHTS["content"] * content_scores
        + WEIGHTS["collaborative"] * cf_scores
    )

    # --------------------------------------------------------
    # Exclude items already seen by this user
    # --------------------------------------------------------

    eligible = np.array(
        [
            int(item_id) not in seen_items
            for item_id in content_ids
        ],
        dtype=bool,
    )

    eligible_indices = np.flatnonzero(eligible)

    if len(eligible_indices) == 0:
        raise RuntimeError(
            "No eligible items remain after excluding seen items."
        )

    top_indices = eligible_indices[top_positive_indices(
        hybrid_scores[eligible_indices], content_ids[eligible_indices], TOP_N
    )]

    recommendations = pd.DataFrame(
        {
            "visitorid": selected_user,
            "rank": np.arange(1, len(top_indices) + 1),
            "itemid": content_ids[top_indices],
            "hybrid_score": hybrid_scores[top_indices],
            "popularity_score": popularity_values[top_indices],
            "content_score": content_scores[top_indices],
            "collaborative_score": cf_scores[top_indices],
        }
    )

    # --------------------------------------------------------
    # Save and display recommendations
    # --------------------------------------------------------

    recommendations.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\n=== TOP HYBRID RECOMMENDATIONS ===")
    print(recommendations.to_string(index=False))

    print(f"\nSaved recommendations to: {OUTPUT_PATH}")
    print("\nDevelopment hybrid run completed.")


if __name__ == "__main__":
    main()

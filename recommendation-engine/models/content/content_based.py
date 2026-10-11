
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import save_npz


# Project paths
ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = DATA_DIR / "processed"

# Use the enhanced features without overwriting the original model
FEATURES_FILE = OUTPUT_DIR / "item_features_enhanced.csv"

MATRIX_FILE = OUTPUT_DIR / "item_tfidf_matrix_enhanced.npz"
VECTORIZER_FILE = OUTPUT_DIR / "item_tfidf_vectorizer_enhanced.joblib"
ITEM_IDS_FILE = OUTPUT_DIR / "item_tfidf_ids_enhanced.csv"


def main():
    print("=== PASAL ENHANCED CONTENT-BASED MODEL ===")

    # 1. Load enhanced item features
    print("\nLoading enhanced item features...")
    items = pd.read_csv(
        FEATURES_FILE,
        usecols=["itemid", "content"],
        dtype={"itemid": "int64", "content": "string"},
    )

    items = items.dropna(subset=["itemid", "content"])
    items = items.drop_duplicates(subset=["itemid"])
    items["content"] = items["content"].astype(str)
    items = items[items["content"].str.strip() != ""]

    if items.empty:
        raise ValueError("No usable enhanced item features were found.")

    print(f"Items with usable features: {len(items):,}")

    # 2. Build TF-IDF vectors
    print("\nBuilding enhanced TF-IDF vectors...")
    vectorizer = TfidfVectorizer(
        lowercase=False,
        token_pattern=r"(?u)\b\w+\b",
        norm="l2",
        dtype=np.float32,
        min_df=2,
        max_features=100_000,
    )

    tfidf_matrix = vectorizer.fit_transform(items["content"])

    # 3. Save separate enhanced model artifacts
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nSaving enhanced TF-IDF matrix...")
    save_npz(MATRIX_FILE, tfidf_matrix)

    print("Saving enhanced TF-IDF vectorizer...")
    joblib.dump(vectorizer, VECTORIZER_FILE)

    print("Saving enhanced item ID mapping...")
    items[["itemid"]].to_csv(ITEM_IDS_FILE, index=False)

    # 4. Report model details
    print("\n=== ENHANCED CONTENT MODEL SUMMARY ===")
    print(f"Items indexed: {tfidf_matrix.shape[0]:,}")
    print(f"TF-IDF features: {tfidf_matrix.shape[1]:,}")
    print(f"Non-zero values: {tfidf_matrix.nnz:,}")
    print(f"Matrix density: {tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1]):.6%}")
    print(f"Matrix file: {MATRIX_FILE}")
    print(f"Vectorizer file: {VECTORIZER_FILE}")
    print(f"Item IDs file: {ITEM_IDS_FILE}")
    print("\nEnhanced content-based model preparation complete.")


if __name__ == "__main__":
    main()

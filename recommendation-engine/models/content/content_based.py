
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import save_npz


# Project paths
DATA_DIR = Path("data")
FEATURES_FILE = DATA_DIR / "processed" / "item_features.csv"

OUTPUT_DIR = DATA_DIR / "processed"
MATRIX_FILE = OUTPUT_DIR / "item_tfidf_matrix.npz"
VECTORIZER_FILE = OUTPUT_DIR / "item_tfidf_vectorizer.joblib"
ITEM_IDS_FILE = OUTPUT_DIR / "item_tfidf_ids.csv"


def main():
    print("=== PASAL CONTENT-BASED MODEL ===")

    # 1. Load prepared item features.
    print("Loading item features...")
    items = pd.read_csv(FEATURES_FILE)

    required_columns = {"itemid", "content"}
    if not required_columns.issubset(items.columns):
        missing = required_columns - set(items.columns)
        raise ValueError(f"Missing required columns: {missing}")

    items = items.dropna(subset=["itemid", "content"])
    items = items.drop_duplicates(subset=["itemid"])
    items["content"] = items["content"].astype(str)

    # Remove rows without usable content.
    items = items[items["content"].str.strip() != ""]

    if items.empty:
        raise ValueError("No usable item features were found.")

    print(f"Items with usable features: {len(items):,}")

    # 2. Convert category tokens into TF-IDF vectors.
    print("Building TF-IDF vectors...")
    vectorizer = TfidfVectorizer(
        lowercase=False,
        token_pattern=r"(?u)\b\w+\b",
        norm="l2",
        dtype="float32",
    )

    tfidf_matrix = vectorizer.fit_transform(items["content"])

    # 3. Save the model artifacts for later use.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Saving TF-IDF matrix...")
    save_npz(MATRIX_FILE, tfidf_matrix)

    print("Saving TF-IDF vectorizer...")
    joblib.dump(vectorizer, VECTORIZER_FILE)

    print("Saving item ID mapping...")
    items[["itemid"]].to_csv(ITEM_IDS_FILE, index=False)

    # 4. Report model details.
    print("\n=== CONTENT MODEL SUMMARY ===")
    print(f"Items indexed: {tfidf_matrix.shape[0]:,}")
    print(f"TF-IDF features: {tfidf_matrix.shape[1]:,}")
    print(f"Non-zero values: {tfidf_matrix.nnz:,}")
    print(f"Matrix file: {MATRIX_FILE}")
    print(f"Vectorizer file: {VECTORIZER_FILE}")
    print(f"Item IDs file: {ITEM_IDS_FILE}")
    print("Content-based model preparation complete.")


if __name__ == "__main__":
    main()
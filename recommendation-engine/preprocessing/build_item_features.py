
import pandas as pd
from pathlib import Path

DATA = Path("data/processed")
OUTPUT_FILE = DATA / "item_features.csv"

print("=== BUILDING PASAL ITEM FEATURES ===")

# Load the validated item-category records
categories = pd.read_csv(DATA / "item_categories.csv")

# Remove duplicate item-category pairs
categories = categories[
    ["itemid", "categoryid", "parentid"]
].drop_duplicates()

# Keep every category associated with each item.
# Multiple categories are combined into a single feature string.
features = (
    categories.groupby("itemid")
    .agg(
        categories=(
            "categoryid",
            lambda values: " ".join(
                f"category_{int(value)}"
                for value in sorted(set(values))
            ),
        ),
        parent_categories=(
            "parentid",
            lambda values: " ".join(
                f"parent_{int(value)}"
                for value in sorted(
                    set(values.dropna())
                )
            ),
        ),
    )
    .reset_index()
)

# Combine category and parent-category features for TF-IDF
features["content"] = (
    features["categories"].fillna("")
    + " "
    + features["parent_categories"].fillna("")
).str.strip()

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
features.to_csv(OUTPUT_FILE, index=False)

print(f"Items with features: {len(features):,}")
print(f"Saved to: {OUTPUT_FILE}")

print("\n=== SAMPLE FEATURES ===")
print(features.head(5).to_string(index=False))

print("\n=== VALIDATION ===")
print(f"Missing content: {features['content'].isna().sum()}")
print(f"Empty content: {(features['content'].str.len() == 0).sum()}")

print("\nDone.")

import pandas as pd
from pathlib import Path

RAW_DATA = Path("data/raw")
PROCESSED_DATA = Path("data/processed")

PROCESSED_DATA.mkdir(parents=True, exist_ok=True)

ITEM_PROPERTIES = PROCESSED_DATA / "item_properties.csv"
CATEGORY_TREE = RAW_DATA / "category_tree.csv"
OUTPUT_FILE = PROCESSED_DATA / "item_categories.csv"

print("=== PASAL CATEGORY PREPROCESSING ===")

# Read the category hierarchy
category_tree = pd.read_csv(CATEGORY_TREE)

category_tree["categoryid"] = pd.to_numeric(
    category_tree["categoryid"], errors="coerce"
)
category_tree["parentid"] = pd.to_numeric(
    category_tree["parentid"], errors="coerce"
)

print(f"Category tree rows: {len(category_tree):,}")

# Extract category properties in chunks to reduce memory use
category_chunks = []

for chunk in pd.read_csv(
    ITEM_PROPERTIES,
    chunksize=500_000
):
    categories = chunk[
        chunk["property"].astype(str) == "categoryid"
    ][["itemid", "value"]].copy()

    if not categories.empty:
        categories["categoryid"] = pd.to_numeric(
            categories["value"], errors="coerce"
        )

        categories = categories.dropna(
            subset=["categoryid"]
        )

        categories["categoryid"] = (
            categories["categoryid"].astype("int64")
        )

        category_chunks.append(
            categories[["itemid", "categoryid"]]
        )

print("Combining extracted categories...")

if category_chunks:
    item_categories = pd.concat(
        category_chunks,
        ignore_index=True
    )

    # Keep one category per item for this initial dataset.
    # We'll inspect conflicts before final model development.
    item_categories = item_categories.drop_duplicates()

    # Attach the category's parent category
    item_categories = item_categories.merge(
        category_tree,
        on="categoryid",
        how="left"
    )

    item_categories.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"Items with category records: {len(item_categories):,}")
    print(
        "Missing parent categories:",
        item_categories["parentid"].isna().sum()
    )
    print(f"Saved to: {OUTPUT_FILE}")
else:
    print("No categoryid properties were found.")

print("Done.")
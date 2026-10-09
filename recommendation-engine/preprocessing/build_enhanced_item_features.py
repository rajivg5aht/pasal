
from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

PROPERTIES_PATH = ROOT / "data" / "processed" / "item_properties.csv"
BASE_FEATURES_PATH = ROOT / "data" / "processed" / "item_features.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "item_features_enhanced.csv"

CHUNK_SIZE = 250_000

# Start with frequently observed properties.
# Property IDs are anonymous, so we treat their values as categorical features.
SELECTED_PROPERTIES = {
    "790",
    "888",
    "available",
    "categoryid",
    "283",
    "6",
    "678",
    "364",
    "776",
    "764",
    "159",
    "112",
    "202",
    "917",
    "839",
    "227",
    "698",
    "689",
    "28",
    "928",
}


def safe_token(value):
    """Convert a property value into a usable text token."""
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value[:80]


def main():
    print("=== PASAL ENHANCED ITEM FEATURES ===")

    print("\nLoading existing category features...")

    base = pd.read_csv(
        BASE_FEATURES_PATH,
        usecols=["itemid", "categories", "parent_categories"],
    )

    base["itemid"] = base["itemid"].astype("int64")

    # Preserve the original category and parent-category features.
    features = {}

    for row in base.itertuples(index=False):
        tokens = []

        if pd.notna(row.categories):
            tokens.extend(str(row.categories).split())

        if pd.notna(row.parent_categories):
            tokens.extend(str(row.parent_categories).split())

        features[int(row.itemid)] = tokens

    print(f"Base items: {len(features):,}")

    print("\nReading selected item properties in chunks...")
    print(f"Selected property IDs: {len(SELECTED_PROPERTIES)}")

    rows_used = 0
    items_enriched = set()

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            PROPERTIES_PATH,
            dtype=str,
            chunksize=CHUNK_SIZE,
        ),
        start=1,
    ):
        chunk = chunk[
            chunk["property"].isin(SELECTED_PROPERTIES)
        ]

        if chunk.empty:
            continue

        chunk = chunk.dropna(subset=["itemid", "property", "value"])

        for row in chunk.itertuples(index=False):
            item_id = int(row.itemid)

            if item_id not in features:
                continue

            property_id = safe_token(row.property)
            value_token = safe_token(row.value)

            if not property_id or not value_token:
                continue

            token = f"prop{property_id}_val_{value_token}"

            features[item_id].append(token)
            rows_used += 1
            items_enriched.add(item_id)

        print(
            f"Processed chunk {chunk_number}; "
            f"property rows used: {rows_used:,}"
        )

    print("\nBuilding enhanced feature file...")

    output = pd.DataFrame(
        {
            "itemid": item_id,
            "content": " ".join(dict.fromkeys(tokens)),
        }
        for item_id, tokens in features.items()
    )

    output.to_csv(OUTPUT_PATH, index=False)

    print("\n=== BUILD SUMMARY ===")
    print(f"Items: {len(output):,}")
    print(f"Property rows used: {rows_used:,}")
    print(f"Items enriched: {len(items_enriched):,}")
    print(f"Unique content combinations: {output['content'].nunique():,}")
    print(f"Output: {OUTPUT_PATH}")
    print("\nEnhanced feature building completed.")


if __name__ == "__main__":
    main()

from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "item_properties.csv"

CHUNK_SIZE = 500_000
MAX_EXAMPLES_PER_PROPERTY = 5


def main():
    print("=== PASAL ITEM PROPERTY INSPECTION ===")
    print("Reading property data in chunks...\n")

    property_counts = Counter()
    item_property_counts = Counter()
    property_examples = {}
    unique_items = set()
    total_rows = 0

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            INPUT_PATH,
            dtype=str,
            chunksize=CHUNK_SIZE,
        ),
        start=1,
    ):
        total_rows += len(chunk)

        chunk["itemid"] = chunk["itemid"]
        chunk["property"] = chunk["property"].fillna("UNKNOWN")
        chunk["value"] = chunk["value"].fillna("")

        property_counts.update(chunk["property"].value_counts().to_dict())
        item_property_counts.update(
            chunk["itemid"].value_counts().to_dict()
        )

        unique_items.update(chunk["itemid"].dropna().unique())

        # Keep only a few real examples per property.
        for property_id, value in zip(
            chunk["property"],
            chunk["value"],
        ):
            examples = property_examples.setdefault(property_id, [])

            if len(examples) < MAX_EXAMPLES_PER_PROPERTY:
                if value not in examples:
                    examples.append(value)

        print(
            f"Processed chunk {chunk_number}: "
            f"{total_rows:,} rows so far"
        )

    print("\n=== OVERALL SUMMARY ===")
    print(f"Total property rows: {total_rows:,}")
    print(f"Unique items: {len(unique_items):,}")
    print(f"Unique properties: {len(property_counts):,}")

    print("\n=== MOST COMMON PROPERTIES ===")

    for property_id, count in property_counts.most_common(20):
        print(
            f"Property: {property_id} | "
            f"Rows: {count:,} | "
            f"Examples: {property_examples.get(property_id, [])}"
        )

    print("\n=== PROPERTIES WITH FEWEST ROWS ===")

    for property_id, count in property_counts.most_common()[-10:]:
        print(
            f"Property: {property_id} | "
            f"Rows: {count:,} | "
            f"Examples: {property_examples.get(property_id, [])}"
        )

    item_counts = pd.Series(list(item_property_counts.values()))

    print("\n=== PROPERTIES PER ITEM ===")
    print(f"Average rows per item: {item_counts.mean():.2f}")
    print(f"Median rows per item: {item_counts.median():.0f}")
    print(f"Maximum rows per item: {item_counts.max():,}")

    print("\nInspection completed. No source data was modified.")


if __name__ == "__main__":
    main()
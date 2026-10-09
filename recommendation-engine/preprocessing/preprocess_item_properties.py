import pandas as pd
from pathlib import Path

RAW_DATA = Path("data/raw")
PROCESSED_DATA = Path("data/processed")

PROCESSED_DATA.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 500_000


def process_file(file_path):
    print(f"\nProcessing: {file_path.name}")

    chunks = []

    for chunk in pd.read_csv(file_path, chunksize=CHUNK_SIZE):
        # Keep the important columns
        chunk = chunk[["itemid", "property", "value"]]

        chunks.append(chunk)

        print(f"Processed {sum(len(c) for c in chunks):,} rows...")

    return pd.concat(chunks, ignore_index=True)


print("=== ITEM PROPERTY PREPROCESSING ===")

part1 = process_file(
    RAW_DATA / "item_properties_part1.csv"
)

part2 = process_file(
    RAW_DATA / "item_properties_part2.csv"
)

print("\nCombining Part 1 and Part 2...")

item_properties = pd.concat(
    [part1, part2],
    ignore_index=True
)

print(f"Total rows: {len(item_properties):,}")

# Remove duplicate item-property-value combinations
item_properties = item_properties.drop_duplicates(
    subset=["itemid", "property", "value"]
)

print(
    f"Rows after removing duplicates: "
    f"{len(item_properties):,}"
)

output_file = PROCESSED_DATA / "item_properties.csv"

item_properties.to_csv(
    output_file,
    index=False
)

print(f"\nSaved to: {output_file}")

print("\n=== FINAL SUMMARY ===")
print(f"Unique items: {item_properties['itemid'].nunique():,}")
print(f"Unique properties: {item_properties['property'].nunique():,}")
print(f"Final rows: {len(item_properties):,}")

print("\nDone.")
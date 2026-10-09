import pandas as pd
from pathlib import Path

RAW_DATA = Path("data/raw")

# ============================================================
# EVENTS DATASET
# ============================================================

events = pd.read_csv(RAW_DATA / "events.csv")

print("=== EVENTS DATASET ===")
print(f"Rows: {len(events):,}")
print(f"Columns: {events.columns.tolist()}")

print("\n=== EVENT TYPES ===")
print(events["event"].value_counts())

print("\n=== UNIQUE USERS ===")
print(f"{events['visitorid'].nunique():,}")

print("\n=== UNIQUE ITEMS ===")
print(f"{events['itemid'].nunique():,}")

print("\n=== MISSING VALUES ===")
print(events.isnull().sum())


# ============================================================
# TIME RANGE
# ============================================================

print("\n=== TIME RANGE ===")

events["datetime"] = pd.to_datetime(events["timestamp"], unit="ms")

print(f"Start: {events['datetime'].min()}")
print(f"End:   {events['datetime'].max()}")


# ============================================================
# CHRONOLOGICAL SPLIT POINTS
# ============================================================

print("\n=== CHRONOLOGICAL SPLIT POINTS ===")

start_time = events["datetime"].min()
end_time = events["datetime"].max()

total_duration = end_time - start_time

train_end = start_time + (total_duration * 0.70)
validation_end = start_time + (total_duration * 0.85)

print(f"Train:      {start_time} → {train_end}")
print(f"Validation: {train_end} → {validation_end}")
print(f"Test:       {validation_end} → {end_time}")


# ============================================================
# ITEM PROPERTIES PART 1
# ============================================================

print("\n=== ITEM PROPERTIES PART 1 ===")

item_part1 = pd.read_csv(
    RAW_DATA / "item_properties_part1.csv",
    nrows=5
)

print("Sample rows:")
print(item_part1)

print(f"Columns: {item_part1.columns.tolist()}")


# ============================================================
# ITEM PROPERTIES PART 2
# ============================================================

print("\n=== ITEM PROPERTIES PART 2 ===")

item_part2 = pd.read_csv(
    RAW_DATA / "item_properties_part2.csv",
    nrows=5
)

print("Sample rows:")
print(item_part2)

print(f"Columns: {item_part2.columns.tolist()}")


# ============================================================
# CATEGORY TREE
# ============================================================

print("\n=== CATEGORY TREE ===")

category_tree = pd.read_csv(
    RAW_DATA / "category_tree.csv"
)

print(f"Rows: {len(category_tree):,}")
print(f"Columns: {category_tree.columns.tolist()}")
print(category_tree.head())
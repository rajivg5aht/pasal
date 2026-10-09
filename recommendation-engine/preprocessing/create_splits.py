import pandas as pd
from pathlib import Path

RAW_DATA = Path("data/raw")
SPLIT_DATA = Path("data/splits")

SPLIT_DATA.mkdir(parents=True, exist_ok=True)

print("Loading events.csv...")

events = pd.read_csv(RAW_DATA / "events.csv")

# Convert timestamp from milliseconds to datetime
events["datetime"] = pd.to_datetime(events["timestamp"], unit="ms")

# Calculate chronological split points
start_time = events["datetime"].min()
end_time = events["datetime"].max()

total_duration = end_time - start_time

train_end = start_time + (total_duration * 0.70)
validation_end = start_time + (total_duration * 0.85)

# Create chronological splits
train = events[events["datetime"] < train_end]
validation = events[
    (events["datetime"] >= train_end) &
    (events["datetime"] < validation_end)
]
test = events[events["datetime"] >= validation_end]

# Save splits
train.to_csv(SPLIT_DATA / "train.csv", index=False)
validation.to_csv(SPLIT_DATA / "validation.csv", index=False)
test.to_csv(SPLIT_DATA / "test.csv", index=False)

print("\n=== SPLIT RESULTS ===")
print(f"Train:      {len(train):,} interactions")
print(f"Validation: {len(validation):,} interactions")
print(f"Test:       {len(test):,} interactions")

print("\n=== SPLIT DATES ===")
print(f"Train ends:      {train_end}")
print(f"Validation ends: {validation_end}")

print("\nSplit files created successfully.")


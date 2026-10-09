
import pandas as pd
from pathlib import Path

DATA = Path("data/processed")
RAW = Path("data/raw")

categories = pd.read_csv(DATA / "item_categories.csv")
tree = pd.read_csv(RAW / "category_tree.csv")

print("=== CATEGORY DATA VALIDATION ===")

print(f"Total category records: {len(categories):,}")
print(f"Unique items: {categories['itemid'].nunique():,}")
print(f"Unique categories used: {categories['categoryid'].nunique():,}")

# Check items with multiple categories
categories_per_item = categories.groupby("itemid")["categoryid"].nunique()

print("\n=== CATEGORIES PER ITEM ===")
print(f"Items with one category: {(categories_per_item == 1).sum():,}")
print(f"Items with multiple categories: {(categories_per_item > 1).sum():,}")

# Check category IDs that do not appear in the category tree
tree_ids = set(tree["categoryid"].dropna())
used_ids = set(categories["categoryid"].dropna())

missing_ids = used_ids - tree_ids

print("\n=== CATEGORY TREE VALIDATION ===")
print(f"Used categories: {len(used_ids):,}")
print(f"Categories absent from tree: {len(missing_ids):,}")

print("\n=== SAMPLE CATEGORY RECORDS ===")
print(categories.head(10).to_string(index=False))

print("\nValidation complete.")
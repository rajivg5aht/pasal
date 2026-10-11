"""Build a new point-in-time catalogue from the existing raw property files.

Never touches event splits. All selected facts have timestamp < cutoff_ms.
The SQLite intermediate bounds memory; conflicting latest values are excluded.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.enrichment import sha, validate_catalogue

ROOT = Path(__file__).resolve().parents[2]
PROPERTIES = {"categoryid", "available", "790", "888", "283", "6", "678", "364", "776",
              "764", "159", "112", "202", "917", "839", "227", "698", "689", "28", "928"}
UPSERT = """
INSERT INTO facts(itemid, property, timestamp, value, source, ambiguous)
VALUES (?, ?, ?, ?, ?, 0)
ON CONFLICT(itemid, property) DO UPDATE SET
  ambiguous=CASE
    WHEN excluded.timestamp > facts.timestamp THEN 0
    WHEN excluded.timestamp = facts.timestamp AND excluded.value != facts.value THEN 1
    ELSE facts.ambiguous END,
  value=CASE WHEN excluded.timestamp > facts.timestamp THEN excluded.value ELSE facts.value END,
  source=CASE WHEN excluded.timestamp > facts.timestamp THEN excluded.source ELSE facts.source END,
  timestamp=MAX(facts.timestamp, excluded.timestamp)
"""


def initialize(connection):
    connection.execute("""CREATE TABLE facts(
        itemid INTEGER NOT NULL, property TEXT NOT NULL, timestamp INTEGER NOT NULL,
        value TEXT NOT NULL, source TEXT NOT NULL, ambiguous INTEGER NOT NULL,
        PRIMARY KEY(itemid, property))""")


def ingest(connection, frame, cutoff_ms, source):
    required = ["timestamp", "itemid", "property", "value"]
    if frame[required].isna().any().any():
        raise ValueError("Missing source timestamp/ID/property/value; repair explicitly before use")
    eligible = frame.loc[(frame.timestamp < cutoff_ms) & frame.property.isin(PROPERTIES)]
    with connection:
        connection.executemany(UPSERT, ((int(r.itemid), str(r.property), int(r.timestamp), str(r.value), source)
                                       for r in eligible.itertuples(index=False)))
    return len(eligible)


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build(paths, cutoff_ms, output_dir, max_items=None, seed=42, chunksize=250_000):
    if cutoff_ms < 1 or chunksize < 1 or (max_items is not None and max_items < 1):
        raise ValueError("Cutoff, chunksize and optional item limit must be positive")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {"version": "metadata-snapshot-v1", "status": "building",
                "cutoff_exclusive_ms": cutoff_ms, "selected_properties": sorted(PROPERTIES),
                "source_sha256": {}, "source_rows": 0, "eligible_property_rows": 0,
                "selection_seed": seed, "max_items": max_items,
                "tie_policy": "exclude a property with conflicting values at its latest timestamp",
                "availability_policy": "record latest available flag; downstream must define/filter candidate availability"}
    with closing(sqlite3.connect(output_dir / "snapshot.sqlite")) as connection:
        initialize(connection)
        for path in map(Path, paths):
            manifest["source_sha256"][path.name] = fingerprint(path)
            for number, chunk in enumerate(pd.read_csv(path, dtype={"timestamp": "int64", "itemid": "int64",
                     "property": "str", "value": "str"}, keep_default_na=False, chunksize=chunksize), 1):
                manifest["source_rows"] += len(chunk)
                manifest["eligible_property_rows"] += ingest(connection, chunk, cutoff_ms, path.name)
                if number % 10 == 0:
                    print(f"{path.name}: {number} chunks processed", flush=True)
        manifest["conflicting_latest_properties_excluded"] = connection.execute(
            "SELECT COUNT(*) FROM facts WHERE ambiguous=1").fetchone()[0]
        item_ids = np.array([row[0] for row in connection.execute(
            "SELECT DISTINCT itemid FROM facts WHERE ambiguous=0 ORDER BY itemid")], dtype=np.int64)
        manifest["eligible_metadata_items"] = len(item_ids)
        if max_items is not None and len(item_ids) > max_items:
            item_ids = np.sort(np.random.default_rng(seed).choice(item_ids, max_items, replace=False))
        selected = set(map(int, item_ids))
        manifest["selected_items"] = len(selected)
        manifest["selected_item_ids_sha256"] = sha(sorted(selected))
        source_hash = sha({"files": manifest["source_sha256"], "cutoff": cutoff_ms,
                           "properties": manifest["selected_properties"], "tie_policy": manifest["tie_policy"]})
        written = invalid = 0
        with (output_dir / "catalogue.jsonl").open("x", encoding="utf-8") as output:
            for itemid in sorted(selected):
                rows = list(connection.execute(
                    "SELECT property,value,timestamp,source FROM facts WHERE itemid=? AND ambiguous=0 ORDER BY property", (itemid,)))
                record = {"itemid": itemid, "as_of_ms": cutoff_ms, "source_sha256": source_hash,
                          "properties": {p:v for p,v,_,_ in rows}}
                try:
                    validate_catalogue(record)
                except ValueError:
                    invalid += 1
                    continue
                output.write(json.dumps(record, sort_keys=True) + "\n")
                written += 1
        manifest.update(status="completed", exported_items=written,
                        items_excluded_by_catalogue_schema=invalid,
                        catalogue_sha256=fingerprint(output_dir / "catalogue.jsonl"))
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoff-ms", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True, help="New version directory only")
    parser.add_argument("--max-items", type=int, help="Optional seeded metadata-only subset; selection uses no events")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    paths = [ROOT / "data/raw/item_properties_part1.csv", ROOT / "data/raw/item_properties_part2.csv"]
    print(json.dumps(build(paths, args.cutoff_ms, args.output_dir, args.max_items, args.seed), indent=2))

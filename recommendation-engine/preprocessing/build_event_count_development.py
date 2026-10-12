"""Versioned 70/15/15 timestamp plan; materialize development partitions only.

Read raw timestamps for boundaries, and already-exposed train/validation events
for development rows. Never open the legacy final test file. Reserve final-test
materialization and evaluation for configuration freeze.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def boundaries(timestamps):
    values = np.asarray(timestamps)
    if len(values) < 10 or not np.issubdtype(values.dtype, np.integer) or (values < 0).any():
        raise ValueError("At least ten nonnegative integer timestamps required")
    ordered = np.sort(values, kind="stable")
    first, second = len(values) * 70 // 100, len(values) * 85 // 100
    a, b = int(ordered[first]), int(ordered[second])
    if a >= b:
        raise ValueError("Insufficient distinct timestamps for chronological partitions")
    # Put a whole tied timestamp into the later partition. Ratios are disclosed.
    counts = [int((values < a).sum()), int(((values >= a) & (values < b)).sum()), int((values >= b).sum())]
    return {"total_events": len(values), "validation_start_ms": a, "test_start_ms": b,
            "nominal_counts": [first, second - first, len(values) - second],
            "effective_counts": counts,
            "boundary_tie_policy": "entire_timestamp_moves_to_later_partition"}


def build(raw_events, legacy_train, legacy_validation, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Existing research artifacts must not be overwritten")
    raw_times = pd.read_csv(raw_events, usecols=["timestamp"]).timestamp
    plan = boundaries(raw_times.to_numpy())
    train = pd.read_csv(legacy_train)
    validation = pd.read_csv(legacy_validation)
    old_end = int(validation.timestamp.max())
    if int(train.timestamp.max()) >= int(validation.timestamp.min()):
        raise ValueError("Legacy development partitions overlap in time")
    if plan["test_start_ms"] > old_end:
        raise ValueError("New development would require untouched test events")
    dev = pd.concat([train, validation], ignore_index=True).sort_values("timestamp", kind="stable")
    a, b = plan["validation_start_ms"], plan["test_start_ms"]
    new_train = dev[dev.timestamp < a]
    new_validation = dev[(dev.timestamp >= a) & (dev.timestamp < b)]
    if [len(new_train), len(new_validation)] != plan["effective_counts"][:2]:
        raise ValueError("Development counts do not match raw timestamp plan")
    exposed = int(((validation.timestamp >= b) & (validation.timestamp <= old_end)).sum())
    plan.update(status="development_only_final_test_not_materialized",
                legacy_validation_end_ms=old_end, previously_exposed_test_events=exposed,
                independent_test_rule=f"timestamp > {old_end}",
                metadata_cutoff_exclusive_ms=a,
                source_sha256={str(p): file_hash(p) for p in [raw_events, legacy_train, legacy_validation]},
                implementation_sha256=file_hash(__file__),
                limitations=["Full planned 15% test has historical validation exposure",
                             "Final confirmatory subset must exclude previously exposed events",
                             "Models and metadata require rebuilding at the new training cutoff"])
    output.mkdir(parents=True, exist_ok=False)
    new_train.to_csv(output / "train.csv", index=False)
    new_validation.to_csv(output / "validation.csv", index=False)
    plan["output_sha256"] = {name: file_hash(output / name) for name in ["train.csv", "validation.csv"]}
    (output / "manifest.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-events", type=Path, default=Path("data/raw/events.csv"))
    parser.add_argument("--legacy-train", type=Path, default=Path("data/splits/train.csv"))
    parser.add_argument("--legacy-validation", type=Path, default=Path("data/splits/validation.csv"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.raw_events, args.legacy_train, args.legacy_validation, args.output), indent=2))

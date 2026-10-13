"""Nested event subsamples of the existing training partition; never reads outcomes."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models.content.train_snapshot import fingerprint


def build(source, output, cutoff_ms, seed=42):
    output = Path(output)
    if output.exists():
        raise FileExistsError('Use a new density version')
    events = pd.read_csv(source)
    if events.empty or events.timestamp.isna().any() or (events.timestamp >= cutoff_ms).any():
        raise ValueError('Training events must precede the declared cutoff')
    if not events.timestamp.is_monotonic_increasing:
        raise ValueError('Require the chronological training file')
    permutation = np.random.default_rng(seed).permutation(len(events))
    original_hash = fingerprint(source)
    output.mkdir(parents=True, exist_ok=False)
    manifests = []
    for percentage in [10, 25, 50]:
        size = len(events)*percentage//100
        if size < 1:
            raise ValueError('Too few events for the declared density')
        # Sorting original row indexes preserves time and original tie order.
        indexes = np.sort(permutation[:size])
        folder = output/f'density-{percentage}'
        folder.mkdir()
        events.iloc[indexes].to_csv(folder/'train.csv', index=False)
        np.save(folder/'source_rows.npy', indexes)
        manifest = {'kind': 'nested_training_event_density', 'percentage': percentage,
                    'seed': seed, 'rows': size, 'original_rows': len(events),
                    'cutoff_exclusive_ms': cutoff_ms, 'original_train_sha256': original_hash,
                    'train_sha256': fingerprint(folder/'train.csv'),
                    'source_rows_sha256': fingerprint(folder/'source_rows.npy'),
                    'selection': 'sorted prefix of one seeded row permutation; nested without replacement',
                    'metadata_policy': 'unchanged historical catalogue and candidate universe',
                    'tuning_policy': 'retain full-density selected settings; no density-specific retuning'}
        (folder/'manifest.json').write_text(json.dumps(manifest, indent=2))
        manifests.append(manifest)
    (output/'manifest.json').write_text(json.dumps({'variants': manifests,
        'full_density': 'reuse original training and its verified CF model'}, indent=2))
    return manifests


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--train', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cutoff-ms', type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.train, args.output, args.cutoff_ms), indent=2))

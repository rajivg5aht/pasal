"""Outcome-blind uniform sample of eligible historical catalogue records."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.enrichment import validate_catalogue
from models.content.train_snapshot import fingerprint


def sample_catalogue(source, output, size=32, seed=42):
    if size < 1:
        raise ValueError("Sample size must be positive")
    output = Path(output)
    if output.exists():
        raise FileExistsError("Use a new sample version")
    rng = random.Random(seed)
    sample, seen, cutoffs = [], set(), set()
    population = 0
    counts = Counter()
    with Path(source).open(encoding="utf-8") as stream:
        for line in stream:
            record = validate_catalogue(json.loads(line))
            if record['itemid'] in seen:
                raise ValueError("Duplicate catalogue item")
            seen.add(record['itemid'])
            cutoffs.add(record['as_of_ms'])
            if record['properties'].get('available') == '0':
                continue
            population += 1
            counts[record['properties'].get('available', 'unknown')] += 1
            if len(sample) < size:
                sample.append(record)
            else:
                position = rng.randrange(population)
                if position < size:
                    sample[position] = record
    if len(cutoffs) != 1 or population < size:
        raise ValueError("Require one cutoff and at least the requested eligible population")
    sample.sort(key=lambda r: r['itemid'])
    output.mkdir(parents=True, exist_ok=False)
    destination = output / 'catalogue.jsonl'
    destination.write_text(''.join(json.dumps(r, sort_keys=True)+'\n' for r in sample), encoding='utf-8')
    manifest = {'design': 'uniform reservoir without replacement; no events or outcomes read',
                'seed': seed, 'size': size, 'eligible_population': population,
                'eligibility': 'historical available != 0; unknown retained',
                'cutoff_ms': next(iter(cutoffs)), 'population_availability': dict(counts),
                'sample_availability': dict(Counter(r['properties'].get('available', 'unknown') for r in sample)),
                'sample_categories': len({r['properties'].get('categoryid') for r in sample}),
                'source_sha256': fingerprint(source), 'sample_sha256': fingerprint(destination),
                'itemids': [r['itemid'] for r in sample],
                'limitations': ['Small quality/feasibility sample; no category-level precision guarantee',
                                'No inference of ranking benefit from generation success',
                                'Failed and rejected records are retained; no replacements']}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--size', type=int, default=32)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(sample_catalogue(args.catalogue, args.output, args.size, args.seed), indent=2))

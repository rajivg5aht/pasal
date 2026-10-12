"""Append reviewed generated-text features without refitting historical properties.

The full catalogue, base columns and eligibility remain unchanged. Unenriched
rows retain their original vectors exactly. This is a partial-coverage ablation.
"""
import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack, save_npz
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from genai.enrichment import approved_text, sha, validate_catalogue
from models.content.train_snapshot import fingerprint


def train(catalogue, base_dir, sample_dir, cache_dir, reviews_path, output, weight=.25):
    # Import here to avoid the engine's train_snapshot import cycle.
    from models.engine import load_artifact
    base_dir, sample_dir, output = Path(base_dir), Path(sample_dir), Path(output)
    if output.exists():
        raise FileExistsError('Use a new enriched artifact version')
    if not np.isfinite(weight) or not 0 < weight <= 1:
        raise ValueError('Generated feature weight must be in (0,1]')
    sample_manifest = json.loads((sample_dir/'manifest.json').read_text())
    sample_path = sample_dir/'catalogue.jsonl'
    if fingerprint(sample_path) != sample_manifest['sample_sha256']:
        raise ValueError('Sample fingerprint mismatch')
    sample = {r['itemid']: r for r in map(json.loads, sample_path.read_text().splitlines())}
    if len(sample) != sample_manifest['size'] or sorted(sample) != sample_manifest['itemids']:
        raise ValueError('Declared sample identity mismatch')
    base, items, base_manifest = load_artifact(base_dir, sample_manifest['cutoff_ms'])
    if base_manifest['kind'] != 'historical_property_tfidf_not_genai':
        raise ValueError('Require unchanged non-GenAI property baseline')
    source_hash = fingerprint(catalogue)
    if source_hash != base_manifest['catalogue_sha256'] or source_hash != sample_manifest['source_sha256']:
        raise ValueError('Sample and baseline must come from exactly the same catalogue')
    # Check actual sample properties against the full source, not just a claimed hash.
    found = set()
    with Path(catalogue).open(encoding='utf-8') as stream:
        for line in stream:
            record = json.loads(line)
            if record['itemid'] in sample:
                if validate_catalogue(record) != sample[record['itemid']]:
                    raise ValueError('Sample properties differ from historical source')
                found.add(record['itemid'])
    if found != set(sample):
        raise ValueError('Sample has items absent from baseline source')
    reviews = {}
    for line in Path(reviews_path).read_text().splitlines():
        review = json.loads(line)
        if review['cache_key'] in reviews:
            raise ValueError('Duplicate review')
        reviews[review['cache_key']] = review
    accepted = {}
    for path in sorted(Path(cache_dir).glob('*.json')):
        result = json.loads(path.read_text())
        identity = result.get('identity', {})
        record = identity.get('catalogue', {})
        item = record.get('itemid')
        review = reviews.get(result.get('cache_key'))
        if item not in sample or not review or review.get('approved') is not True:
            continue
        if (record != sample[item] or identity.get('provider') != 'groq_free'
                or result.get('source_kind') != 'generative_api'
                or identity.get('model') != 'openai/gpt-oss-20b'
                or sha(identity) != result.get('cache_key') or path.stem != result['cache_key']):
            raise ValueError('Invalid approved generation provenance')
        if item in accepted:
            raise ValueError('Multiple approved outputs for one item')
        accepted[item] = {'text': approved_text(result, review), 'generation': result, 'review': review}
    if not accepted:
        raise ValueError('At least one real, explicitly reviewed generation is required')
    ids = items.itemid.astype(int).tolist()
    rows = [i for i, item in enumerate(ids) if item in accepted]
    vectorizer = TfidfVectorizer(lowercase=True, dtype=np.float32, norm='l2', min_df=1)
    small = vectorizer.fit_transform([accepted[ids[i]]['text'] for i in rows]).tocoo()
    generated = csr_matrix((small.data, (np.asarray(rows)[small.row], small.col)),
                           shape=(len(ids), small.shape[1]), dtype=np.float32)
    combined = hstack([base, generated * weight], format='csr')
    # Normalize only treated rows to preserve every other baseline row bit-for-bit.
    treated = np.array(rows)
    norm = np.sqrt(np.asarray(combined.multiply(combined).sum(axis=1)).ravel())
    scales = np.ones(len(ids), dtype=np.float32)
    scales[treated] = np.divide(1., norm[treated], out=np.ones(len(treated), dtype=np.float32), where=norm[treated] != 0)
    combined = combined.multiply(scales[:, None]).tocsr()
    output.mkdir(parents=True, exist_ok=False)
    save_npz(output/'matrix.npz', combined)
    (output/'items.csv').write_bytes((base_dir/'items.csv').read_bytes())
    joblib.dump(vectorizer, output/'generated_vectorizer.joblib')
    (output/'reviewed_descriptions.json').write_text(json.dumps(accepted, indent=2), encoding='utf-8')
    manifest = {'kind': 'historical_properties_plus_reviewed_generative_text',
                'cutoff_exclusive_ms': sample_manifest['cutoff_ms'], 'catalogue_sha256': source_hash,
                'base_manifest_sha256': fingerprint(base_dir/'manifest.json'),
                'sample_manifest_sha256': fingerprint(sample_dir/'manifest.json'),
                'reviews_sha256': fingerprint(reviews_path), 'generated_weight': weight,
                'rows': len(ids), 'base_features': base.shape[1], 'generated_features': generated.shape[1],
                'approved_items': len(accepted), 'sample_size': len(sample),
                'coverage_fraction': len(accepted)/len(ids),
                'limitations': ['Partial-catalogue treatment; report actual profile and candidate exposure',
                                'Assistant grounding review is not independent human quality assessment',
                                'Fixed .25 weight is a development choice, not a test-tuned optimum',
                                'Boilerplate similarity may harm ranking; no semantic recovery of anonymous codes']}
    manifest['artifacts_sha256'] = {name: fingerprint(output/name) for name in
        ['matrix.npz', 'items.csv', 'generated_vectorizer.joblib', 'reviewed_descriptions.json']}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['catalogue', 'base-dir', 'sample-dir', 'cache-dir', 'reviews-path', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--weight', type=float, default=.25)
    args = parser.parse_args()
    print(json.dumps(train(**vars(args)), indent=2))

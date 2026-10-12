"""Operational generation evidence; never label schema checks as human ratings."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.enrichment import approved_text, sha
from models.content.train_snapshot import fingerprint


def wilson(successes, total):
    if total == 0:
        return None
    z = 1.959963984540054
    proportion = successes/total
    denominator = 1+z*z/total
    center = (proportion+z*z/(2*total))/denominator
    half = z*math.sqrt(proportion*(1-proportion)/total+z*z/(4*total*total))/denominator
    return [max(0., center-half), min(1., center+half)]


def report(sample, cache, reviews_path=None):
    sample = Path(sample)
    declaration = json.loads((sample/'manifest.json').read_text())
    source = sample/'catalogue.jsonl'
    if fingerprint(source) != declaration['sample_sha256']:
        raise ValueError('Declared sample changed')
    records = {r['itemid']: r for r in map(json.loads, source.read_text().splitlines())}
    reviews = {}
    if reviews_path is not None:
        for line in Path(reviews_path).read_text().splitlines():
            review = json.loads(line)
            if review['cache_key'] in reviews:
                raise ValueError('Duplicate review')
            reviews[review['cache_key']] = review
    rows = []
    seen = set()
    for path in sorted(Path(cache).glob('*.json')):
        result = json.loads(path.read_text())
        identity = result.get('identity', {})
        record = identity.get('catalogue', {})
        item = record.get('itemid')
        if item not in records:
            continue
        if (record != records[item] or result.get('source_kind') != 'generative_api'
                or identity.get('provider') != 'groq_free' or sha(identity) != path.stem
                or result.get('cache_key') != path.stem):
            raise ValueError('Invalid sample response provenance')
        if item in seen:
            raise ValueError('Multiple attempts/model versions per item require separate reporting')
        seen.add(item)
        review = reviews.get(path.stem)
        if review:
            if review.get('output_sha256') != sha(result['output']):
                raise ValueError('Review does not match exact output')
            if review.get('approved') is True:
                approved_text(result, review)
        metadata = result.get('provider_metadata', {})
        rows.append({'itemid': item, 'cache_key': path.stem, 'status': result['status'],
                     'http_status': metadata.get('http_status'), 'error_code': metadata.get('error_code'),
                     'usage': metadata.get('usage'), 'latency_ms': result['latency_ms'],
                     'review_decision': review.get('approved') if review else None,
                     'reviewer': review.get('reviewer') if review else None})
    generated = sum(r['status'] == 'generated_pending_review' for r in rows)
    approved = sum(r['review_decision'] is True for r in rows)
    return {'status': 'complete_sample' if len(rows) == len(records) else 'incomplete_sample',
            'sample_size': len(records), 'attempted': len(rows), 'not_attempted': len(records)-len(rows),
            'generated_schema_pass': generated, 'failed_or_rejected': len(rows)-generated,
            'schema_pass_rate_among_attempts': generated/len(rows) if rows else None,
            'schema_pass_wilson_95_interval': wilson(generated, len(rows)),
            'reviewed_approved': approved, 'reviewed_rejected': sum(r['review_decision'] is False for r in rows),
            'pending_review': sum(r['status'] == 'generated_pending_review' and r['review_decision'] is None for r in rows),
            'reported_input_tokens': sum((r['usage'] or {}).get('input_tokens', 0) for r in rows),
            'reported_output_tokens': sum((r['usage'] or {}).get('output_tokens', 0) for r in rows),
            'attempts_without_usage': sum(r['usage'] is None for r in rows),
            'http_status_counts': dict(Counter(str(r['http_status']) for r in rows if r['http_status'] is not None)),
            'sample_manifest_sha256': fingerprint(sample/'manifest.json'), 'attempts': rows,
            'cost': 'Free account attested; no paid fallback. No independent billing statement collected.',
            'limitations': ['Schema pass is not factual consistency, hallucination rate or human relevance',
                           'Incomplete samples cannot support a full-sample quality estimate',
                           'Token totals exclude unavailable failure usage and are lower bounds',
                           'Assistant grounding review must not be represented as independent human ratings']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = report(args.sample, args.cache, args.reviews)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in result.items() if k != 'attempts'}, indent=2))

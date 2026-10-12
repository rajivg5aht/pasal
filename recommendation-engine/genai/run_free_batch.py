"""Resume a declared catalogue sample; wait only before unsent quota reservations.

Provider failures are cached and never retried. A failed API call stops the batch.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.enrichment import cache_lock, cached_enrichment, validate_catalogue
from genai.free_provider import FreeQuota, GroqFreeProvider, QuotaPaused
from models.content.train_snapshot import fingerprint


def run(sample, cache, max_new_requests):
    sample, cache = Path(sample), Path(cache)
    manifest = json.loads((sample/'manifest.json').read_text())
    source = sample/'catalogue.jsonl'
    if fingerprint(source) != manifest['sample_sha256']:
        raise ValueError('Declared sample fingerprint mismatch')
    records = [validate_catalogue(json.loads(s)) for s in source.read_text().splitlines()]
    if len(records) != manifest['size'] or [r['itemid'] for r in records] != manifest['itemids']:
        raise ValueError('Declared sample identity mismatch')
    if max_new_requests < 1:
        raise ValueError('Positive request cap required')
    provider = GroqFreeProvider()
    new = 0
    with cache_lock(cache):
        quota = FreeQuota(cache/'free_quota_reservations.jsonl', provider)
        for record in records:
            if new >= max_new_requests:
                break
            while True:
                try:
                    result, hit = cached_enrichment(record, provider, cache, quota)
                    break
                except QuotaPaused as pause:
                    if pause.retry_after is None:
                        print(str(pause), flush=True)
                        return
                    print(f'Waiting {pause.retry_after:.1f}s for local minute quota; no request sent', flush=True)
                    time.sleep(min(60, pause.retry_after))
            new += not hit
            print(f"item={record['itemid']} status={result['status']} cache_hit={hit}", flush=True)
            if result['status'] != 'generated_pending_review' and not result.get('provider_metadata'):
                print('Stopped on provider failure; no automatic retry', flush=True)
                return
    print(f'Batch stopped/completed with {new} new requests; review required', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--max-new-requests', type=int, default=32)
    parser.add_argument('--live', action='store_true', required=True)
    args = parser.parse_args()
    # Only the two authorized provider settings are loaded; never print values.
    env_path = Path(__file__).resolve().parents[2]/'.env'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            key, separator, value = line.partition('=')
            if separator and key in {'GROQ_API_KEY', 'GROQ_ACCOUNT_TIER'}:
                os.environ.setdefault(key, value.strip().strip('\"').strip("'"))
    if os.environ.get('GROQ_ACCOUNT_TIER') != 'free' or not os.environ.get('GROQ_API_KEY'):
        raise ValueError('Configure a verified Free account locally')
    run(args.sample, args.cache, args.max_new_requests)

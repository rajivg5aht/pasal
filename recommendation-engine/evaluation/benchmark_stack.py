"""Bounded anonymous public-API diagnostic; no accounts, cookies or writes."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
from urllib.parse import urlparse

import numpy as np
import requests

PATHS = ['/api/products', '/api/categories', '/api/recommendations']


def validate_response(path, data):
    key = {'/api/products': 'products', '/api/categories': 'categories',
           '/api/recommendations': 'items'}[path]
    values = data[key]
    if not isinstance(values, list):
        raise ValueError('Expected array')
    if path == '/api/recommendations':
        ids = [row['itemid'] for row in values]
        if len(ids) != len(set(ids)) or len(ids) > 10:
            raise ValueError('Duplicate or oversized recommendations')
        if any(row['product']['_id'] != row['itemid'] or row['product']['available'] is not True for row in values):
            raise ValueError('Recommendation hydration mismatch')
        if data['strategy'] != 'global_popularity':
            raise ValueError('Anonymous request unexpectedly personalized')
    return len(values)


def run(base, output, count=24):
    parsed = urlparse(base)
    if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
            or parsed.port != 3000 or parsed.path not in ['', '/']
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError('Only the local public backend at port 3000 is allowed')
    if type(count) is not int or count < 3 or count > 30 or count % 3:
        raise ValueError('Use 3..30 requests per phase, divisible by three')
    output = Path(output)
    if output.exists():
        raise FileExistsError('Use a new diagnostic version')

    def request(index):
        path = PATHS[index % 3]
        row = {'path': path, 'valid': False}
        started = time.perf_counter()
        try:
            response = requests.get(base.rstrip('/')+path, timeout=(3, 15), allow_redirects=False)
            row['status'] = response.status_code
            if response.status_code == 200:
                row['returned_items'] = validate_response(path, response.json())
                row['valid'] = True
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            row['error'] = type(error).__name__
            row.setdefault('status', 'transport_error')
        row['latency_ms'] = (time.perf_counter()-started)*1000
        return row

    warmup = [request(i) for i in range(3)]
    if not all(row['valid'] for row in warmup):
        raise RuntimeError('Warm-up failed; inspect local services before benchmarking')
    phases = []
    for concurrency in [1, 2, 4]:
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            rows = list(executor.map(request, range(count)))
        wall = time.perf_counter()-started
        summaries = []
        for path in PATHS:
            attempted = [r for r in rows if r['path'] == path]
            successes = [r for r in attempted if r['valid']]
            latencies = [r['latency_ms'] for r in successes]
            summaries.append({'path': path, 'attempts': len(attempted), 'valid_successes': len(successes),
                              'status_counts': dict(Counter(str(r['status']) for r in attempted)),
                              'success_p50_ms': float(np.median(latencies)) if latencies else None,
                              'success_p95_ms': float(np.quantile(latencies, .95)) if latencies else None,
                              'minimum_returned_items': min((r['returned_items'] for r in successes), default=None)})
        phases.append({'concurrency': concurrency, 'wall_seconds': wall,
                       'valid_requests_per_second': sum(r['valid'] for r in rows)/wall,
                       'routes': summaries, 'rows': rows})
    report = {'status': 'development_anonymous_public_api_diagnostic',
              'warmup_requests': 3, 'requests_per_phase': count, 'phases': phases,
              'limitations': ['Includes Express, recommendation service and MongoDB response hydration',
                             'Excludes browser rendering, signed-in sessions and personalization flows',
                             'Small mixed-route load with concurrent background work; not final controlled performance evidence',
                             'No credentials, cookies, accounts or mutations; failures retained without retry']}
    output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    return [{k: v for k, v in phase.items() if k != 'rows'} for phase in phases]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:3000')
    parser.add_argument('--count', type=int, default=24)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))

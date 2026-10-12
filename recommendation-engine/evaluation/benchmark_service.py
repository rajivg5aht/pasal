"""Bounded localhost-only development load diagnostic; no accounts or writes."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import platform
import threading
import time
from urllib.parse import urlparse

import numpy as np
import psutil
import requests

PROFILES = [
    {'personalization': False},
    {'personalization': True, 'event_count': 1, 'recent_items': [5411], 'seen_items': [5411]},
    {'personalization': True, 'event_count': 25, 'recent_items': [5411, 461686], 'seen_items': [5411, 461686]},
]


def run(url, token, count, concurrency, output, service_pid=None):
    parsed = urlparse(url)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.username or parsed.password or parsed.query:
        raise ValueError('Only explicit localhost HTTP service URLs are allowed')
    if not 3 <= count <= 300 or not concurrency or any(c not in [1, 2, 4] for c in concurrency):
        raise ValueError('Bounded 3..300 requests per phase; concurrency only 1,2,4')
    if len(token) < 32:
        raise ValueError('Service credential required locally')
    output = Path(output)
    if output.exists():
        raise FileExistsError('Use a new benchmark version')
    headers = {'X-Service-Token': token}
    process = psutil.Process(service_pid) if service_pid else None
    phases = []

    def request(index):
        started = time.perf_counter()
        result = {'profile': ['anonymous', 'low_history', 'warm_history'][index % 3]}
        try:
            response = requests.post(url, json=PROFILES[index % 3], headers=headers, timeout=(3, 15), allow_redirects=False)
            result['status'] = response.status_code
            if response.status_code == 200:
                data = response.json()
                result.update(strategy=data['strategy'], items=len(data['items']),
                              cutoff_ms=data['model_cutoff_ms'], genai_used=data['genai_used'])
        except (requests.RequestException, ValueError, KeyError) as error:
            result.update(status='client_error', error=type(error).__name__)
        result['latency_ms'] = (time.perf_counter()-started)*1000
        return result

    # Explicit unmeasured warm-up, no retry of individual failures.
    warmup = [request(i) for i in range(3)]
    if any(r['status'] != 200 for r in warmup):
        raise RuntimeError('Warm-up failed; do not interpret a load benchmark against an unavailable service')
    for workers in concurrency:
        stop = threading.Event()
        memory = []
        def monitor():
            while not stop.is_set():
                if process:
                    memory.append(process.memory_info().rss)
                stop.wait(.05)
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.start()
        before_cpu = process.cpu_times() if process else None
        started = time.perf_counter()
        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                rows = list(executor.map(request, range(count)))
        finally:
            stop.set()
            monitor_thread.join()
        wall = time.perf_counter()-started
        after_cpu = process.cpu_times() if process else None
        success = [r for r in rows if r['status'] == 200]
        latencies = [r['latency_ms'] for r in success]
        phases.append({'concurrency': workers, 'requests': count, 'successes': len(success),
                       'status_counts': dict(Counter(str(r['status']) for r in rows)),
                       'successful_requests_per_second': len(success)/wall,
                       'attempted_requests_per_second': count/wall, 'wall_seconds': wall,
                       'success_p50_ms': float(np.median(latencies)) if latencies else None,
                       'success_p95_ms': float(np.quantile(latencies, .95)) if latencies else None,
                       'all_attempt_p95_ms': float(np.quantile([r['latency_ms'] for r in rows], .95)),
                       'service_peak_sampled_rss_bytes': max(memory) if memory else None,
                       'service_cpu_seconds': ((after_cpu.user+after_cpu.system)-(before_cpu.user+before_cpu.system)) if process else None,
                       'rows': rows})
    report = {'status': 'development_local_service_diagnostic', 'warmup_requests': 3,
              'host': {'os': platform.system(), 'logical_cpus': psutil.cpu_count(),
                       'ram_bytes': psutil.virtual_memory().total}, 'phases': phases,
              'limitations': ['Synthetic profiles, not user behavior or ranking-quality evidence',
                             'FastAPI only; excludes browser, Express and database latency',
                             'Concurrent background work may affect timings; not final controlled performance results',
                             'RSS is sampled and may miss brief peaks; no GPU usage measured']}
    output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    return [{k: v for k, v in phase.items() if k != 'rows'} for phase in phases]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000/recommendations')
    parser.add_argument('--count', type=int, default=30)
    parser.add_argument('--concurrency', type=int, nargs='+', default=[1, 2, 4])
    parser.add_argument('--service-pid', type=int)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get('RECOMMENDATION_SERVICE_TOKEN', '')
    if not token:
        for line in (Path(__file__).resolve().parents[2]/'.env').read_text().splitlines():
            if line.startswith('RECOMMENDATION_SERVICE_TOKEN='):
                token = line.partition('=')[2].strip()
    print(json.dumps(run(args.url, token, args.count, args.concurrency, args.output, args.service_pid), indent=2))

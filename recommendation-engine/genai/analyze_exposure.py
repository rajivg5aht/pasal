"""Training-only enrichment feasibility; never reads future events or calls an API."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.enrichment import validate_catalogue
from genai.free_provider import GroqFreeProvider, reservation_tokens
from models.content.train_snapshot import fingerprint
from switching.policy import PolicyConfig


def profiles(training, cutoff, policy):
    columns = ['timestamp', 'visitorid', 'itemid']
    if training[columns].isna().any().any() or (training.timestamp >= cutoff).any():
        raise ValueError('Missing identifiers or future training events')
    counts = training.groupby('visitorid').size()
    users = counts[(counts > 0) & (counts < policy.low_history_threshold)].index
    rows = training[training.visitorid.isin(users)]
    return (rows.sort_values('timestamp', kind='stable')
            .drop_duplicates(['visitorid', 'itemid'], keep='last')
            .groupby('visitorid', sort=False).tail(20)), len(counts), len(users)


def compare(training, records, config, sizes=(32, 128, 256, 512), seed=42):
    policy = PolicyConfig(**config['switching'])
    profile, total_users, content_users = profiles(training, config['cutoff_ms'], policy)
    eligible = {}
    seen = set()
    for source in records:
        row = validate_catalogue(source)
        if row['itemid'] in seen or row['as_of_ms'] != config['cutoff_ms']:
            raise ValueError('Duplicate catalogue item or inconsistent cutoff')
        seen.add(row['itemid'])
        if row['properties'].get('available') != '0':
            eligible[row['itemid']] = row
    if not sizes or any(type(n) is not int or n < 1 or n > len(eligible) for n in sizes):
        raise ValueError('Requested sizes must fit eligible catalogue')
    support = profile.groupby('itemid').visitorid.nunique().to_dict()
    uniform = sorted(eligible)
    random.Random(seed).shuffle(uniform)
    targeted = sorted(eligible, key=lambda item: (-support.get(item, 0), item))
    provider = GroqFreeProvider()  # Payload construction only; no credentials/network.
    results, selections = [], {}
    for design, ordered in [('uniform_catalogue', uniform), ('training_profile_support', targeted)]:
        for size in sorted(set(sizes)):
            selected = ordered[:size]
            covered = int(profile[profile.itemid.isin(selected)].visitorid.nunique())
            reserves = [reservation_tokens(provider, eligible[item]) for item in selected]
            key = f'{design}-{size}'
            selections[key] = sorted(selected)
            results.append({'design': design, 'size': size,
                            'content_route_training_users_exposed': covered,
                            'content_route_training_user_exposure_fraction': covered/content_users if content_users else None,
                            'items_with_content_profile_support': sum(support.get(i, 0) > 0 for i in selected),
                            'known_categories': len({eligible[i]['properties']['categoryid'] for i in selected
                                                     if 'categoryid' in eligible[i]['properties']}),
                            'local_reserved_tokens': sum(reserves),
                            'oversized_records_not_sendable': sum(r > 7000 for r in reserves),
                            'fresh_quota_days_lower_bound': max(math.ceil(size/900), math.ceil(sum(reserves)/180000)),
                            'minute_windows_lower_bound': max(math.ceil(size/20), math.ceil(sum(reserves)/7000))})
    aggregate = {'status': 'training_only_feasibility_not_effectiveness', 'seed': seed,
                 'training_users': total_users, 'content_route_training_users': content_users,
                 'content_route_users_with_eligible_profile_item': int(profile[profile.itemid.isin(eligible)].visitorid.nunique()),
                 'eligible_catalogue_items': len(eligible), 'comparisons': results,
                 'limitations': ['Training exposure is in-sample and may not generalize to future users',
                                'Targeted selection favors frequent low-history profile items, not a representative catalogue sample',
                                'Raw event counts determine routing; zero-history users have no content profile',
                                'Availability restricts enrichment selection, not retained user history',
                                'Exposure assumes every selected output is generated and approved; not ranking benefit',
                                'Quota estimates assume fresh local windows, no other usage; packing/provider limits may add time',
                                'Oversized records cannot be sent under the current local guard']}
    return aggregate, selections


def run(train, catalogue, tuning_dir, quality_report, output):
    output, tuning_dir = Path(output), Path(tuning_dir)
    if output.exists():
        raise FileExistsError('Use a new version; preserve the declared analysis')
    config = json.loads((tuning_dir/'selected_config.json').read_text())
    tuning = json.loads((tuning_dir/'manifest.json').read_text())
    train_hash, catalogue_hash = fingerprint(train), fingerprint(catalogue)
    # Manifest keys identify roles; do not accept a matching validation fingerprint.
    expected_train = [v for k, v in tuning['inputs_sha256'].items() if Path(k.replace('\\', '/')).name == 'train.csv']
    if expected_train != [train_hash] or catalogue_hash != tuning['content_manifest']['catalogue_sha256']:
        raise ValueError('Training/catalogue provenance mismatch')
    with Path(catalogue).open(encoding='utf-8') as stream:
        result, selections = compare(pd.read_csv(train), (json.loads(line) for line in stream), config)
    usage = json.loads(Path(quality_report).read_text())
    known = usage['attempted'] - usage['attempts_without_usage']
    result['pilot_usage'] = {'attempts_with_reported_usage': known,
                             'attempts_without_usage': usage['attempts_without_usage'],
                             'mean_reported_tokens_per_usage_known_attempt':
                                 (usage['reported_input_tokens']+usage['reported_output_tokens'])/known if known else None,
                             'interpretation': 'Observed usage subset only; do not impute missing failure usage'}
    result['inputs_sha256'] = {str(p): fingerprint(p) for p in
                              [train, catalogue, tuning_dir/'manifest.json', tuning_dir/'selected_config.json', quality_report]}
    result['source_sha256'] = fingerprint(__file__)
    result['quota_source'] = {'url': 'https://console.groq.com/docs/rate-limits',
                              'checked_date': '2026-10-13', 'model': provider_model(),
                              'published_free': {'rpm': 30, 'rpd': 1000, 'tpm': 8000, 'tpd': 200000},
                              'local_guard': {'rpm': 20, 'rpd': 900, 'tpm': 7000, 'tpd': 180000}}
    output.mkdir(parents=True)
    (output/'selections.json').write_text(json.dumps(selections, indent=2), encoding='utf-8')
    result['selections_sha256'] = fingerprint(output/'selections.json')
    (output/'report.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    return result


def provider_model():
    return GroqFreeProvider().model


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['train', 'catalogue', 'tuning-dir', 'quality-report', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))

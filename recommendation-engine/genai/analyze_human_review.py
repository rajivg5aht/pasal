"""Validate returned review packets and summarize recorded ratings without imputation."""
import argparse
from collections import Counter
from datetime import date
import hashlib
import itertools
import json
from pathlib import Path
import re

COUNTS = ('supported_assertions', 'unsupported_assertions', 'unassessable_assertions')
SCALES = ('clarity_1_to_5', 'usefulness_1_to_5')
SEVERITY = 'unsupported_claim_severity'
FIELDS = (*COUNTS, *SCALES, SEVERITY, 'notes')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(template, returned):
    code = returned.get('reviewer_code')
    if not isinstance(code, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', code):
        raise ValueError('Supply a non-identifying reviewer_code (letters/numbers/_/-)')
    try:
        date.fromisoformat(returned['review_date'])
    except (KeyError, TypeError, ValueError):
        raise ValueError('Supply review_date as YYYY-MM-DD') from None
    for key in ('rubric', 'instructions'):
        if returned.get(key) != template[key]:
            raise ValueError('Review instructions or rubric changed')
    expected = {c['case_id']: c for c in template['cases']}
    cases = returned.get('cases', [])
    ids = [c.get('case_id') for c in cases]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError('Every original case must appear exactly once')
    for case in cases:
        original = expected[case['case_id']]
        for key in ('historical_source_properties', 'generated_output'):
            if case.get(key) != original[key]:
                raise ValueError('Source facts or generated text changed')
        ratings = case.get('ratings', {})
        if set(ratings) != set(FIELDS):
            raise ValueError('Rating fields changed')
        for key in (*COUNTS, *SCALES):
            value = ratings[key]
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError('Ratings must be integers or null; booleans are invalid')
            if key in SCALES and value is not None and not 1 <= value <= 5:
                raise ValueError('Ordinal ratings must be between 1 and 5')
        if ratings[SEVERITY] not in (None, 'none', 'minor', 'major', 'unassessable'):
            raise ValueError('Unknown unsupported-claim severity')
        if ratings['notes'] is not None and not isinstance(ratings['notes'], str):
            raise ValueError('Notes must be text or null')
        if ratings['unsupported_assertions'] == 0 and ratings[SEVERITY] in ('minor', 'major'):
            raise ValueError('Unsupported severity conflicts with zero unsupported assertions')
        if (ratings['unsupported_assertions'] or 0) > 0 and ratings[SEVERITY] == 'none':
            raise ValueError('Unsupported assertions conflict with severity none')
    return code, {c['case_id']: c['ratings'] for c in cases}


def summarize(packet, rating_files):
    packet = Path(packet)
    manifest = json.loads((packet/'manifest.json').read_text(encoding='utf-8'))
    template_path = packet/'reviewer-template.json'
    if digest(template_path) != manifest['template_sha256']:
        raise ValueError('Original reviewer template fingerprint changed')
    template = json.loads(template_path.read_text(encoding='utf-8'))
    reviewers, summaries, provenance = {}, {}, []
    for path in rating_files:
        returned = json.loads(Path(path).read_text(encoding='utf-8'))
        code, cases = validate(template, returned)
        if code in reviewers:
            raise ValueError('Duplicate reviewer code; preserve independent initial ratings')
        reviewers[code] = cases
        complete = [r for r in cases.values() if all(r[k] is not None for k in COUNTS[:2])]
        supported = sum(r[COUNTS[0]] for r in complete)
        unsupported = sum(r[COUNTS[1]] for r in complete)
        summaries[code] = {
            'cases': len(cases),
            'missing_by_field': {k: sum(r[k] is None for r in cases.values()) for k in FIELDS},
            'factual_consistency': {
                'cases_with_both_counts': len(complete),
                'zero_assessable_cases': sum(r[COUNTS[0]] + r[COUNTS[1]] == 0 for r in complete),
                'supported': supported, 'unsupported': unsupported,
                'pooled_assertion_fraction': supported/(supported+unsupported) if supported+unsupported else None,
                'definition': 'Supported / (supported + unsupported), only cases with both counts present',
            },
            'unassessable_assertions_reported': sum(r[COUNTS[2]] or 0 for r in cases.values()),
            'distributions': {k: dict(Counter(str(r[k]) for r in cases.values() if r[k] is not None))
                              for k in (*SCALES, SEVERITY)},
        }
        provenance.append({'reviewer_code': code, 'review_date': returned['review_date'], 'sha256': digest(path)})
    comparisons = []
    for first, second in itertools.combinations(reviewers, 2):
        fields = {}
        for field in (*COUNTS, *SCALES, SEVERITY):
            paired = [(case_id, a[field], reviewers[second][case_id][field])
                      for case_id, a in reviewers[first].items()
                      if a[field] is not None and reviewers[second][case_id][field] is not None]
            fields[field] = {
                'paired_cases': len(paired),
                'exact_matches': sum(a == b for _, a, b in paired),
                'disagreement_cases': [c for c, a, b in paired if a != b],
            }
        comparisons.append({'reviewers': [first, second], 'fields': fields})
    observed = sum(r[k] is not None for cases in reviewers.values() for r in cases.values()
                   for k in (*COUNTS, *SCALES, SEVERITY))
    return {
        'status': 'recorded_ratings_not_identity_verified' if observed else 'no_ratings_recorded',
        'template_sha256': manifest['template_sha256'],
        'failed_generations_not_rateable': manifest['failed_attempts_not_rateable'],
        'review_files': provenance, 'per_reviewer': summaries, 'pairwise_exact_comparisons': comparisons,
        'limitations': ['Files do not prove reviewer identity, independence, consent or ethics approval.',
                       'Missing ratings remain missing; unassessable claims are excluded from factual consistency.',
                       'Exact comparisons are descriptive, not chance-corrected agreement or adjudication.',
                       'Do not pool targeted and uniform sampling studies.'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--ratings', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.packet, args.ratings)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(result['status'])

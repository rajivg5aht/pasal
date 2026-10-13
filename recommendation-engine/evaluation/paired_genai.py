"""Seven-condition validation diagnostic with honest partial-GenAI exposure.

Uses the existing disjoint assessment users and selected settings, without tuning
on their outcomes. This is not the frozen final holdout experiment.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.common import prepare_cases, cohort, ranking_metrics, summarize
from evaluation.tune_baselines import CONFIGURATIONS, COHORTS
from models.engine import RecommendationEngine
from models.content.train_snapshot import fingerprint
from switching.policy import PolicyConfig


def paired_interval(rows, first='switching_with_genai', second='switching_without_genai', resamples=2000):
    """Paired user bootstrap; overall estimate gives each observed cohort equal weight."""
    frame = pd.DataFrame(rows)
    left = frame[frame.model == first].set_index('visitorid')
    right = frame[frame.model == second].set_index('visitorid')
    if left.index.has_duplicates or right.index.has_duplicates or set(left.index) != set(right.index):
        raise ValueError('Exactly matched unique users required')
    right = right.reindex(left.index)
    if not left.cohort.equals(right.cohort):
        raise ValueError('Cohorts differ across paired conditions')
    rng = np.random.default_rng(42)
    deltas = left.ndcg - right.ndcg
    groups = [deltas[left.cohort == label].to_numpy() for label in COHORTS]
    groups = [g for g in groups if len(g)]
    if not groups:
        raise ValueError('Nonempty paired users required')
    samples = np.mean([rng.choice(g, size=(resamples, len(g)), replace=True).mean(axis=1) for g in groups], axis=0)
    return {'comparison': f'{first} minus {second}', 'users': len(left),
            'mean_ndcg_difference_equal_cohort_weight': float(np.mean([g.mean() for g in groups])),
            'bootstrap_95_percentile_interval': np.quantile(samples, [.025, .975]).tolist(),
            'resamples': resamples, 'seed': 42,
            'limitations': 'Development diagnostic, not a final hypothesis test; zero exposure is uninformative'}


def run(train, validation, content_dir, enriched_dir, cf_dir, tuning_dir, output, training_variant=None):
    output, tuning_dir = Path(output), Path(tuning_dir)
    if output.exists():
        raise FileExistsError('Use a new diagnostic version')
    config = json.loads((tuning_dir/'selected_config.json').read_text())
    tuning = json.loads((tuning_dir/'manifest.json').read_text())
    # Require exact data used for the documented tuning/assessment partition.
    expected = set(tuning['inputs_sha256'].values())
    if not {fingerprint(train), fingerprint(validation)} <= expected:
        raise ValueError('Diagnostic inputs differ from tuning provenance')
    source_training, outcomes = pd.read_csv(train), pd.read_csv(validation)
    assessment = {r['visitorid'] for r in tuning['sample'] if r['partition'] == 'assessment'}
    original_counts = source_training[source_training.visitorid.isin(assessment)].groupby('visitorid').size().to_dict()
    original_items = set(source_training.itemid)
    actual_train, density_manifest = Path(train), None
    if training_variant is not None:
        variant = Path(training_variant)
        density_manifest = json.loads((variant/'manifest.json').read_text())
        actual_train = variant/'train.csv'
        if (density_manifest.get('kind') != 'nested_training_event_density'
                or density_manifest['original_train_sha256'] != fingerprint(train)
                or density_manifest['train_sha256'] != fingerprint(actual_train)
                or density_manifest['cutoff_exclusive_ms'] != config['cutoff_ms']):
            raise ValueError('Density training provenance mismatch')
        training = pd.read_csv(actual_train)
    else:
        training = source_training
    base = RecommendationEngine(training, config['cutoff_ms'], content_dir, cf_dir)
    enriched = RecommendationEngine(training, config['cutoff_ms'], enriched_dir, cf_dir)
    # A density intervention removes interactions, not catalogue knowledge.
    stable_candidates = frozenset((original_items | set(base.content_ids)) - base.unavailable)
    base.eligible = enriched.eligible = stable_candidates
    if base.eligible != enriched.eligible or not np.array_equal(base.content_ids, enriched.content_ids):
        raise ValueError('Paired candidate universes differ')
    if enriched.content_manifest['base_manifest_sha256'] != fingerprint(Path(content_dir)/'manifest.json'):
        raise ValueError('Enriched model does not extend this exact baseline')
    if base.cf_manifest['train_sha256'] != fingerprint(actual_train):
        raise ValueError('CF training provenance mismatch')
    generated = set(map(int, json.loads((Path(enriched_dir)/'reviewed_descriptions.json').read_text())))
    assessment = {r['visitorid'] for r in tuning['sample'] if r['partition'] == 'assessment'}
    cases = [c for c in prepare_cases(training, outcomes, config['cutoff_ms']) if c.visitorid in assessment]
    if {c.visitorid for c in cases} != assessment:
        raise ValueError('Assessment user partition mismatch')
    rows, exposure = [], []
    started = time.perf_counter()
    policy = PolicyConfig(**config['switching'])
    for index, case in enumerate(cases, 1):
        signals, confidence, selected = base.signals(case)
        enhanced_signals, enhanced_confidence, enhanced_selected = enriched.signals(case)
        rankings = {}
        for name in CONFIGURATIONS + ['switching_with_genai']:
            engine, current, conf, categories = ((enriched, enhanced_signals, enhanced_confidence, enhanced_selected)
                if name == 'switching_with_genai' else (base, signals, confidence, selected))
            recs, strategy = engine.predict(case, current, conf, categories, name, policy, config['fixed_weights'])
            if len(set(recs)) != len(recs) or not set(recs) <= base.eligible - case.seen:
                raise ValueError('Invalid paired recommendation')
            rankings[name] = recs
            rows.append({'model': name, 'visitorid': case.visitorid, 'cohort': cohort(case.event_count),
                         'original_cohort': cohort(int(original_counts.get(case.visitorid, 0))),
                         'history_events': case.event_count, 'targetless': not bool(case.targets),
                         'target_count': len(case.targets), 'eligible_target_count': len(case.targets & base.eligible - case.seen),
                         'recommendations': recs, 'strategy': strategy, 'failure': None, 'latency_ms': None,
                         **ranking_metrics(recs, case.targets, 10),
                         **{'eligible_'+k: v for k, v in ranking_metrics(recs, case.targets & base.eligible - case.seen, 10).items()}})
        exposure.append({'visitorid': case.visitorid, 'cohort': cohort(case.event_count),
                         'generated_profile_items': len(set(case.history) & generated),
                         'generated_candidates': len(generated & (base.eligible - case.seen)),
                         'generated_recommendations': len(set(rankings['switching_with_genai']) & generated),
                         'content_route': strategy == 'content',
                         'ranking_changed': rankings['switching_with_genai'] != rankings['switching_without_genai']})
        if index % 25 == 0:
            print(f'Evaluated {index}/{len(cases)} shared users', flush=True)
    output.mkdir(parents=True, exist_ok=False)
    for name, values in [('per_user', rows), ('exposure', exposure)]:
        (output/(name+'.jsonl')).write_text(''.join(json.dumps(r, allow_nan=False)+'\n' for r in values))
    report = {'status': 'partial_enrichment_validation_diagnostic_not_final_H2',
              'summaries': summarize(rows, base.eligible),
              'original_cohort_summaries': summarize([{**r, 'cohort': r['original_cohort']} for r in rows], base.eligible),
              'cohort_migration': dict(Counter(cohort(int(original_counts.get(c.visitorid, 0)))+' -> '+cohort(c.event_count) for c in cases)),
              'density_manifest': density_manifest, 'candidate_universe_size': len(stable_candidates),
              'paired': paired_interval(rows),
              'exposure': {'users': len(cases), 'profile_exposed_users': sum(r['generated_profile_items'] > 0 for r in exposure),
                           'users_with_generated_recommendations': sum(r['generated_recommendations'] > 0 for r in exposure),
                           'changed_rankings': sum(r['ranking_changed'] for r in exposure),
                           'content_routed_users': sum(r['content_route'] for r in exposure),
                           'generated_profile_and_content_routed_users': sum(r['content_route'] and r['generated_profile_items'] > 0 for r in exposure),
                           'approved_items': len(generated)},
              'inputs_sha256': {str(p): fingerprint(p) for p in [train, validation, tuning_dir/'selected_config.json',
                  Path(content_dir)/'manifest.json', Path(enriched_dir)/'manifest.json', Path(cf_dir)/'manifest.json']},
              'total_wall_seconds': time.perf_counter()-started,
              'limitations': ['Shared signal computation does not measure independent request latency',
                              'Small, partially enriched catalogue; no final test or representative H2 claim']}
    (output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    return report['exposure']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['train', 'validation', 'content-dir', 'enriched-dir', 'cf-dir', 'tuning-dir', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--training-variant', type=Path)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))

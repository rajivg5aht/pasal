"""Freeze inputs before materializing holdout outcomes; run all seven fixed conditions."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.common import prepare_cases, cohort, ranking_metrics, summarize
from evaluation.final_statistics import analyze, COHORTS
from evaluation.tune_baselines import CONFIGURATIONS
from evaluation.analyze_density import diversity
from genai.quality_report import report as quality_report
from models.engine import RecommendationEngine
from models.content.train_snapshot import fingerprint
from switching.policy import PolicyConfig

ROOT = Path(__file__).resolve().parents[2]


def require_complete(evidence):
    if (evidence['status'] != 'complete_sample' or evidence['not_attempted'] != 0
            or evidence['pending_review'] != 0 or evidence['reviewed_approved'] < 1):
        raise ValueError('Finish the declared generation attempts and exact grounding reviews before final freeze')


def select_cases(cases, per_cohort, seed):
    if type(per_cohort) is not int or per_cohort < 1:
        raise ValueError('Positive cohort sample size required')
    rng = np.random.default_rng(seed)
    selected = []
    population = {}
    for label in COHORTS:
        group = sorted([c for c in cases if cohort(c.event_count) == label], key=lambda c: c.visitorid)
        population[label] = len(group)
        indices = rng.permutation(len(group))[:per_cohort]
        selected.extend(group[i] for i in indices)
    if not selected:
        raise ValueError('Empty holdout population')
    return selected, population


def require_paired_validation(report_path, inputs, assessment_users):
    """Require the exact treatment's validation evidence without selecting on its scores."""
    report_path = Path(report_path)
    evidence = json.loads(report_path.read_text())
    if (evidence.get('status') != 'partial_enrichment_validation_diagnostic_not_final_H2'
            or evidence.get('density_manifest') is not None):
        raise ValueError('Full-density paired validation required')
    recorded = {str(Path(p).resolve()): digest for p, digest in evidence['inputs_sha256'].items()}
    for path in inputs:
        if recorded.get(str(path.resolve())) != fingerprint(path):
            raise ValueError('Paired validation input mismatch: ' + str(path))
    outputs = [report_path.parent/name for name in ('per_user.jsonl', 'exposure.jsonl')]
    for path in outputs:
        if evidence.get('outputs_sha256', {}).get(path.name) != fingerprint(path):
            raise ValueError('Paired validation output mismatch: ' + path.name)
    rows = [json.loads(line) for line in outputs[0].read_text().splitlines()]
    models = set(CONFIGURATIONS + ['switching_with_genai'])
    users = {}
    for row in rows:
        observed = users.setdefault(row['visitorid'], set())
        if row['model'] in observed or row.get('failure'):
            raise ValueError('Duplicate or failed paired validation case')
        observed.add(row['model'])
    if not users or any(observed != models for observed in users.values()):
        raise ValueError('All seven configurations must assess the same users')
    if len(users) != evidence['exposure']['users']:
        raise ValueError('Paired validation user count mismatch')
    if set(users) != set(assessment_users):
        raise ValueError('Paired validation assessment partition mismatch')
    exposure = [json.loads(line) for line in outputs[1].read_text().splitlines()]
    if len(exposure) != len(users) or {row['visitorid'] for row in exposure} != set(users):
        raise ValueError('Paired validation exposure users mismatch')
    return outputs


def freeze(output, enriched, sample, reviews, paired_validation, per_cohort=500):
    output, enriched, sample, reviews = map(Path, (output, enriched, sample, reviews))
    if output.exists():
        raise FileExistsError('Never overwrite a final freeze')
    if per_cohort < 1:
        raise ValueError('Positive cohort sample size required')
    quality = quality_report(sample, ROOT/'data/enriched/groq-free-v1', reviews)
    require_complete(quality)
    paths = {'raw_events': ROOT/'data/raw/events.csv',
        'split': ROOT/'data/splits/event-count-v1/manifest.json',
        'train': ROOT/'data/splits/event-count-v1/train.csv',
        'validation': ROOT/'data/splits/event-count-v1/validation.csv',
        'paired_validation': Path(paired_validation),
        'config': ROOT/'data/processed/validation-tuning-v2/selected_config.json',
        'tuning_manifest': ROOT/'data/processed/validation-tuning-v2/manifest.json',
        'validation_summary': ROOT/'data/processed/validation-tuning-v2/summary.json',
        'base': ROOT/'data/processed/content-event-count-v1/manifest.json',
        'cf': ROOT/'data/processed/cf-event-count-v1/manifest.json',
        'enriched': enriched/'manifest.json', 'sample': sample/'manifest.json', 'reviews': reviews}
    enhanced = json.loads(paths['enriched'].read_text())
    if (enhanced['sample_manifest_sha256'] != fingerprint(paths['sample'])
            or enhanced['reviews_sha256'] != fingerprint(reviews)
            or enhanced['base_manifest_sha256'] != fingerprint(paths['base'])
            or enhanced['approved_items'] != quality['reviewed_approved']):
        raise ValueError('Final enriched artifact does not match the completed reviewed sample')
    tuning = json.loads(paths['tuning_manifest'].read_text())
    assessment_users = {row['visitorid'] for row in tuning['sample'] if row['partition'] == 'assessment'}
    paired_outputs = require_paired_validation(paths['paired_validation'],
        [paths[key] for key in ('train', 'validation', 'config', 'tuning_manifest', 'base', 'cf', 'enriched')],
        assessment_users)
    # Snapshot every implementation and every model file, not just top-level manifests.
    extra = list((ROOT/'recommendation-engine').rglob('*.py')) + paired_outputs
    for key in ('base', 'cf', 'enriched'):
        manifest = json.loads(paths[key].read_text())
        extra += [paths[key].parent/name for name in manifest['artifacts_sha256']]
    files = {str(p.resolve().relative_to(ROOT)): fingerprint(p) for p in [*paths.values(), *extra]}
    config = json.loads(paths['config'].read_text())
    validation_summary = json.loads(paths['validation_summary'].read_text())
    baseline_scores = {}
    for model in CONFIGURATIONS[:-1]:
        group = [r for r in validation_summary if r['model'] == model and r['cohort'] in ('1-4', '5-19') and r['users']]
        if len(group) != 2:
            raise ValueError('Both H1 validation cohorts required for baseline selection')
        baseline_scores[model] = float(np.mean([r['ndcg'] for r in group]))
    best_baseline = max(baseline_scores, key=baseline_scores.get)
    if best_baseline != 'fixed_hybrid':
        raise ValueError('Primary comparator must be updated prospectively to the validation-best baseline')
    plan = json.loads(paths['split'].read_text())
    if config['cutoff_ms'] != plan['metadata_cutoff_exclusive_ms']:
        raise ValueError('Configuration origin does not match split')
    if fingerprint(paths['raw_events']) not in set(plan['source_sha256'].values()):
        raise ValueError('Raw events differ from the original split plan')
    if fingerprint(paths['train']) != plan['output_sha256']['train.csv']:
        raise ValueError('Training partition differs from the original split plan')
    spec = {'status': 'frozen_before_holdout_materialization',
        'code_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'paths': {k: str(p.resolve().relative_to(ROOT)) for k, p in paths.items()},
        'files_sha256': files, 'seed': 42, 'per_cohort': per_cohort,
        'sampling': 'Seeded uniform without replacement within each original-training event-count cohort; at most per_cohort; all available if smaller',
        'configurations': CONFIGURATIONS + ['switching_with_genai'], 'k': 10,
        'config': config, 'generation_evidence': quality,
        'history_policy': 'Fixed original 70% training histories/models/metadata; validation events are not added or used to refit',
        'populations': {'full_15_percent': 'Historically exposed secondary analysis',
                        'untouched_intersection': 'Primary comparisons; timestamp strictly after legacy validation end'},
        'statistics': {'primary': ['switching_without_genai - fixed_hybrid', 'switching_with_genai - switching_without_genai'],
            'H1_cohorts': ['1-4', '5-19'], 'H2_cohorts': ['0', '1-4', '5-19'],
            'validation_baseline_scores_H1': baseline_scores,
            'metric': 'NDCG@10, equal weight across observed hypothesis cohorts', 'bootstrap': 2000,
            'paired_label_swap_permutations_max': 9999, 'holm_family_alpha': .05},
        'human_ratings': 'Deferred; no independent human-quality claim',
        'limitations': ['Static training-origin histories imply a longer forecast horizon for test than validation.',
                       'Stratified evaluation is not population-frequency-weighted effectiveness.',
                       'The full 15% includes previously exposed validation events; only the intersection is untouched.']}
    with output.open('x', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, allow_nan=False)
    return spec


def verify(spec):
    if spec.get('status') != 'frozen_before_holdout_materialization':
        raise ValueError('A final freeze is required')
    for path, expected in spec['files_sha256'].items():
        if fingerprint(ROOT/path) != expected:
            raise ValueError('Frozen input changed: ' + path)


def run(frozen, output):
    frozen, output = Path(frozen), Path(output)
    if output.exists():
        raise FileExistsError('Never overwrite holdout outcomes')
    spec = json.loads(frozen.read_text())
    verify(spec)  # Must run before reading any holdout outcome fields.
    paths = {k: ROOT/v for k, v in spec['paths'].items()}
    config = spec['config']
    plan = json.loads(paths['split'].read_text())
    training = pd.read_csv(paths['train'])
    base = RecommendationEngine(training, config['cutoff_ms'], paths['base'].parent, paths['cf'].parent)
    enhanced = RecommendationEngine(training, config['cutoff_ms'], paths['enriched'].parent, paths['cf'].parent)
    if base.eligible != enhanced.eligible or not np.array_equal(base.content_ids, enhanced.content_ids):
        raise ValueError('Paired item universes differ')
    if base.cf_manifest['train_sha256'] != fingerprint(paths['train']):
        raise ValueError('CF training provenance mismatch')
    # Original row order breaks equal-timestamp ties; legacy files remain untouched.
    events = pd.read_csv(paths['raw_events']).sort_values('timestamp', kind='stable')
    outcomes = events[events.timestamp >= plan['test_start_ms']]
    if len(outcomes) != plan['effective_counts'][2]:
        raise ValueError('Holdout count mismatch')
    exposed = outcomes.timestamp <= plan['legacy_validation_end_ms']
    if int(exposed.sum()) != plan['previously_exposed_test_events']:
        raise ValueError('Historical exposure count mismatch')
    generated = set(map(int, json.loads((paths['enriched'].parent/'reviewed_descriptions.json').read_text())))
    item_rows = {int(item): i for i, item in enumerate(base.content_ids)}
    policy = PolicyConfig(**config['switching'])
    output.mkdir(parents=True)
    outcomes.to_csv(output/'test.csv', index=False)
    summaries = {}
    for name, subset in [('full_15_percent', outcomes), ('untouched_intersection', outcomes[~exposed])]:
        cases, population = select_cases(prepare_cases(training, subset, config['cutoff_ms']), spec['per_cohort'], spec['seed'])
        rows, exposures = [], []
        for index, case in enumerate(cases, 1):
            prepared, failures = {}, {}
            for kind, engine in [('base', base), ('genai', enhanced)]:
                try:
                    prepared[kind] = engine.signals(case)
                except Exception as error:
                    failures[kind] = type(error).__name__
            rankings, strategies = {}, {}
            for model in spec['configurations']:
                kind = 'genai' if model == 'switching_with_genai' else 'base'
                engine = enhanced if kind == 'genai' else base
                failure = failures.get(kind)
                recs, strategy = [], None
                if failure is None:
                    try:
                        signals, confidence, selected = prepared[kind]
                        recs, strategy = engine.predict(case, signals, confidence, selected, model, policy, config['fixed_weights'], spec['k'])
                        if len(recs) > spec['k'] or len(set(recs)) != len(recs) or not set(recs) <= base.eligible - case.seen:
                            raise ValueError('Invalid recommendations')
                    except Exception as error:
                        failure, recs = type(error).__name__, []
                rankings[model], strategies[model] = recs, strategy
                rows.append({'model': model, 'visitorid': case.visitorid, 'cohort': cohort(case.event_count),
                    'history_events': case.event_count, 'targetless': not bool(case.targets),
                    'target_count': len(case.targets), 'eligible_target_count': len(case.targets & (base.eligible-case.seen)),
                    'failure': failure, 'recommendations': recs, 'strategy': strategy, 'latency_ms': None,
                    **ranking_metrics(recs, case.targets, spec['k']),
                    **{'eligible_'+k: v for k, v in ranking_metrics(recs, case.targets & (base.eligible-case.seen), spec['k']).items()},
                    'diversity': diversity(recs, base.content, item_rows)})
            exposures.append({'visitorid': case.visitorid, 'generated_profile_items': len(set(case.history) & generated),
                'content_route': strategies['switching_with_genai'] == 'content',
                'generated_recommendations': len(set(rankings['switching_with_genai']) & generated),
                'ranking_changed': rankings['switching_with_genai'] != rankings['switching_without_genai']})
            if index % 25 == 0: print(f'{name}: {index}/{len(cases)}', flush=True)
        for suffix, records in [('per_user', rows), ('exposure', exposures)]:
            (output/f'{name}-{suffix}.jsonl').write_text(''.join(json.dumps(r, allow_nan=False)+'\n' for r in records))
        metrics = summarize(rows, base.eligible)
        for aggregate in metrics:
            subset_rows = [r for r in rows if r['model'] == aggregate['model'] and
                           (aggregate['cohort'] == 'all' or r['cohort'] == aggregate['cohort'])]
            for metric in ('precision', 'recall', 'ndcg', 'map', 'hit_rate'):
                aggregate['eligible_'+metric] = float(np.mean([r['eligible_'+metric] for r in subset_rows])) if subset_rows else None
            values = [r['diversity']['value'] for r in subset_rows if r['diversity']['value'] is not None]
            aggregate['mean_common_property_diversity'] = float(np.mean(values)) if values else None
            aggregate['diversity_assessable_users'] = len(values)
        summaries[name] = {'population_users_by_cohort': population, 'sampled_users': len(cases),
            'metrics': metrics, 'paired_statistics': analyze(rows),
            'statistical_role': spec['populations'][name], 'profile_exposed_users': sum(r['generated_profile_items'] > 0 for r in exposures),
            'content_and_profile_exposed_users': sum(r['content_route'] and r['generated_profile_items'] > 0 for r in exposures),
            'changed_rankings': sum(r['ranking_changed'] for r in exposures)}
    result = {'status': 'completed_frozen_holdout_evaluation', 'freeze_sha256': fingerprint(frozen),
              'populations': summaries, 'limitations': spec['limitations'],
              'outputs_sha256': {p.name: fingerprint(p) for p in output.iterdir() if p.is_file()}}
    (output/'report.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    create = subs.add_parser('freeze')
    for key in ('output', 'enriched', 'sample', 'reviews'): create.add_argument('--'+key, type=Path, required=True)
    create.add_argument('--per-cohort', type=int, default=500)
    create.add_argument('--paired-validation', type=Path, required=True)
    execute = subs.add_parser('run')
    execute.add_argument('--frozen', type=Path, required=True)
    execute.add_argument('--output', type=Path, required=True)
    args = vars(parser.parse_args())
    command = args.pop('command')
    result = freeze(**args) if command == 'freeze' else run(**args)
    print(result['status'])

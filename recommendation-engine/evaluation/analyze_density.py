"""Descriptive stable-novelty sensitivity and common-space diversity analysis.

This postprocessing never reranks items or changes fitted models. It is explicitly
secondary, not a replacement for the declared density metrics.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.common import prepare_cases, ranking_metrics, summarize
from evaluation.paired_genai import paired_interval
from models.engine import load_artifact
from models.content.train_snapshot import fingerprint


def diversity(recommendations, matrix, item_rows):
    total_pairs = len(recommendations)*(len(recommendations)-1)//2
    indexes = [item_rows[i] for i in recommendations if i in item_rows]
    indexes = [i for i in indexes if matrix.indptr[i+1] > matrix.indptr[i]]
    valid_pairs = len(indexes)*(len(indexes)-1)//2
    if not valid_pairs:
        return {'value': None, 'valid_pairs': 0, 'total_pairs': total_pairs}
    subset = matrix[indexes]
    similarities = (subset@subset.T).toarray()
    values = similarities[np.triu_indices(len(indexes), 1)]
    return {'value': float(1-np.clip(values, 0, 1).mean()),
            'valid_pairs': valid_pairs, 'total_pairs': total_pairs}


def analyze(suite_dir, output, tuning_dir=None):
    suite_dir, output = Path(suite_dir), Path(output)
    if output.exists():
        raise FileExistsError('Use a new analysis version')
    root = Path(__file__).resolve().parents[2]
    suite = json.loads((suite_dir/'report.json').read_text())
    if {r['density_percent'] for r in suite['densities']} != {10, 25, 50, 100}:
        raise ValueError('Require all four densities')
    tuning_dir = Path(tuning_dir) if tuning_dir else root/'data/processed/validation-tuning-v1'
    tuning_path = tuning_dir/'manifest.json'
    if suite.get('tuning_manifest_sha256', fingerprint(tuning_path)) != fingerprint(tuning_path):
        raise ValueError('Tuning provenance differs from suite')
    tuning = json.loads(tuning_path.read_text())
    ids = {r['visitorid'] for r in tuning['sample'] if r['partition'] == 'assessment'}
    train_path = root/'data/splits/event-count-v1/train.csv'
    validation_path = root/'data/splits/event-count-v1/validation.csv'
    expected = set(tuning['inputs_sha256'].values())
    if not {fingerprint(train_path), fingerprint(validation_path)} <= expected:
        raise ValueError('Original inputs differ from assessment provenance')
    training, validation = pd.read_csv(train_path), pd.read_csv(validation_path)
    # Filter users only for reconstructing cases, retaining ALL their original events.
    cases = prepare_cases(training[training.visitorid.isin(ids)], validation[validation.visitorid.isin(ids)], 1438558255147)
    if {c.visitorid for c in cases} != ids:
        raise ValueError('Assessment users differ')
    targets = {c.visitorid: c.targets for c in cases}
    matrix, items, _ = load_artifact(root/'data/processed/content-event-count-v1', 1438558255147)
    item_rows = {int(item): i for i, item in enumerate(items.itemid)}
    results = []
    for density in suite['densities']:
        folder = suite_dir/f"evaluation-{density['density_percent']}"
        if fingerprint(folder/'report.json') != density['report_sha256']:
            raise ValueError('Suite report changed')
        rows = [json.loads(line) for line in (folder/'per_user.jsonl').read_text().splitlines()]
        if len(rows) != len(ids)*7 or {r['visitorid'] for r in rows} != ids:
            raise ValueError('Missing model/user observations')
        seen = {(r['model'], r['visitorid']) for r in rows}
        if len(seen) != len(rows):
            raise ValueError('Duplicate model/user observations')
        stable_rows, group_diversity = [], defaultdict(list)
        for row in rows:
            original_targets = targets[row['visitorid']]
            stable_rows.append({**row, 'cohort': row['original_cohort'],
                                'target_count': len(original_targets), 'targetless': not bool(original_targets),
                                **ranking_metrics(row['recommendations'], original_targets, 10)})
            group_diversity[row['model']].append(diversity(row['recommendations'], matrix, item_rows))
        # summarize uses only the length of this argument for catalogue coverage.
        summaries = summarize(stable_rows, range(density['candidate_universe_size']))
        diversity_summary = []
        for model, values in sorted(group_diversity.items()):
            assessed = [v['value'] for v in values if v['value'] is not None]
            total = sum(v['total_pairs'] for v in values)
            valid = sum(v['valid_pairs'] for v in values)
            diversity_summary.append({'model': model, 'mean_intra_list_diversity': float(np.mean(assessed)) if assessed else None,
                                      'assessed_lists': len(assessed), 'unassessable_lists': len(values)-len(assessed),
                                      'feature_pair_coverage': valid/total if total else None})
        results.append({'density_percent': density['density_percent'], 'stable_novelty_summaries': summaries,
                        'common_property_space_diversity': diversity_summary,
                        'descriptive_paired_ndcg_original_cohort_weight': [
                            paired_interval([{**r, 'cohort': r['original_cohort']} for r in rows],
                                            first='switching_without_genai', second=comparator)
                            for comparator in ['fixed_hybrid', 'category_popularity', 'global_popularity']
                        ]})
    report = {'status': 'secondary_descriptive_analysis_not_replacement_primary_metrics', 'results': results,
              'suite_sha256': fingerprint(suite_dir/'report.json'), 'source_sha256': fingerprint(__file__),
              'definitions': {'stable_novelty': 'future targets minus FULL original training seen set; no changes to recommendations',
                              'diversity': 'one minus mean off-diagonal cosine in unchanged historical property TF-IDF space'},
              'limitations': ['Secondary analysis chosen to explain novelty-denominator changes after seeing density migration',
                             'Anonymous-code TF-IDF distance is not human semantic diversity',
                             'Missing/empty vectors are unassessable; excluded pairs and lists are reported',
                             'Paired baseline intervals use primary targets and equal ORIGINAL cohort weight; post-hoc, no multiplicity adjustment or confirmatory significance claims',
                             'Models, thresholds and ranking outputs are unchanged']}
    output.write_text(json.dumps(report, indent=2, allow_nan=False))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tuning-dir', type=Path)
    args = parser.parse_args()
    analyze(args.suite, args.output, args.tuning_dir)
    print('Wrote secondary stable-novelty and diversity evidence')

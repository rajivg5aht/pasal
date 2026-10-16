"""Export measured final tables only from a completed, hash-verified evaluation."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models.content.train_snapshot import fingerprint


def export(report_path, frozen, output):
    report_path, frozen, output = map(Path, (report_path, frozen, output))
    if output.exists():
        raise FileExistsError('Preserve earlier thesis tables')
    report = json.loads(report_path.read_text())
    if report.get('status') != 'completed_frozen_holdout_evaluation':
        raise ValueError('Completed final evaluation required')
    if report['freeze_sha256'] != fingerprint(frozen):
        raise ValueError('Final freeze mismatch')
    for name, digest in report['outputs_sha256'].items():
        path = (report_path.parent/name).resolve()
        if path.parent != report_path.parent.resolve() or fingerprint(path) != digest:
            raise ValueError('Final output hash mismatch')
    lines = ['# Final evaluation tables', '',
             'Generated from measured artifacts. These tables do not establish the compound hypotheses by ranking significance alone.', '',
             f'Report SHA256: `{fingerprint(report_path)}`',
             f'Freeze SHA256: `{fingerprint(frozen)}`', '']
    for name in ('untouched_intersection', 'full_15_percent'):
        population = report['populations'][name]
        lines += [f'## {name}', '', population['statistical_role'], '',
                  f"Sampled users: {population['sampled_users']}. Population counts: {json.dumps(population['population_users_by_cohort'], sort_keys=True)}.", '',
                  '| Model | Cohort | Users | Precision@10 | Recall@10 | NDCG@10 | MAP@10 | Hit rate@10 |',
                  '|---|---|---:|---:|---:|---:|---:|---:|']
        for row in population['metrics']:
            values = [row['model'], row['cohort'], str(row['users'])]
            values += ['Not estimable' if row.get(metric) is None else f'{row[metric]:.6f}'
                       for metric in ('precision', 'recall', 'ndcg', 'map', 'hit_rate')]
            lines.append('| ' + ' | '.join(values) + ' |')
        lines += ['', '### Prespecified paired comparisons', '',
                  '| Comparison | Users | Equal-cohort NDCG difference | Marginal 95% bootstrap interval | Holm-adjusted p |',
                  '|---|---:|---:|---|---:|']
        for row in population['paired_statistics']['comparisons']:
            low, high = row['paired_bootstrap_95_percentile_interval']
            lines.append(f"| {row['first']} minus {row['second']} | {row['users']} | {row['equal_cohort_mean_ndcg_difference']:.6f} | [{low:.6f}, {high:.6f}] | {row['holm_p']:.6f} |")
        lines += ['', f"Generated-profile exposure: {population['profile_exposed_users']} users; content-route and profile exposure: {population['content_and_profile_exposed_users']}; changed rankings: {population['changed_rankings']}.", '',
                  'A small p-value with a negative difference is evidence against improvement. A nonsignificant result is not proof of equivalence. The exposed secondary partition cannot override the primary result.', '']
    lines += ['## Limitations', ''] + ['- '+s for s in report['limitations']]
    lines += ['- Independent human quality ratings were deferred; assistant screening is not a replacement.',
              '- Density robustness and end-to-end latency require their separate evidence.', '']
    with output.open('x', encoding='utf-8') as stream:
        stream.write('\n'.join(lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('report', 'frozen', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    export(args.report, args.frozen, args.output)

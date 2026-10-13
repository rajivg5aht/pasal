"""Export a standalone development figure from completed density evidence."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LABELS = {
    'global_popularity': ('Global popularity', '#777777', 'o', '-'),
    'category_popularity': ('Category popularity', '#b56815', 's', '-'),
    'tfidf': ('Property TF-IDF', '#368363', '^', '-'),
    'item_cf': ('Item CF', '#8462ab', 'v', '-'),
    'fixed_hybrid': ('Fixed hybrid', '#3972b5', 'D', '-'),
    'switching_without_genai': ('Switching', '#c4524e', 'o', '-'),
    'switching_with_genai': ('Switching + partial GenAI', '#562323', 'x', '--'),
}


def plot(source, output):
    evidence = json.loads(Path(source).read_text())
    densities = sorted(evidence['densities'], key=lambda r: r['density_percent'])
    if [r['density_percent'] for r in densities] != [10, 25, 50, 100]:
        raise ValueError('Require all four completed declared densities')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    table = []
    for density in densities:
        for summary in density['summaries']:
            if summary['cohort'] == 'all':
                table.append({'density_percent': density['density_percent'], **summary})
    if len(table) != 28 or {row['model'] for row in table} != set(LABELS):
        raise ValueError('Require seven models at every density')
    with (output/'aggregate_metrics.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    with plt.rc_context({'font.family': 'DejaVu Sans', 'font.size': 10}):
        fig, ax = plt.subplots(figsize=(9, 5.5))
        for model, (label, color, marker, style) in LABELS.items():
            values = [r for r in table if r['model'] == model]
            ax.plot([r['density_percent'] for r in values], [r['ndcg'] for r in values],
                    label=label, color=color, marker=marker, linestyle=style, linewidth=1.6, markersize=6)
        ax.set(xlabel='Retained training events (%)', ylabel='Mean NDCG@10', xticks=[10, 25, 50, 100])
        ax.set_ylim(bottom=0)
        ax.grid(alpha=.2)
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(loc='upper center', bbox_to_anchor=(.5, -.16), ncol=3, frameon=False, fontsize=9)
        fig.suptitle('Validation sensitivity to retained training history', x=.12, ha='left', fontsize=14)
        ax.set_title('200 fixed assessment users; 21 reviewed enriched items; development results', loc='left', fontsize=10)
        fig.text(.12, .025, 'Novel targets are recomputed from retained history. Overlapping curves do not establish GenAI equivalence.', fontsize=8)
        fig.subplots_adjust(left=.12, right=.97, top=.83, bottom=.28)
        fig.savefig(output/'density-ndcg.png', dpi=180)
        fig.savefig(output/'density-ndcg.pdf')
        plt.close(fig)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(plot(args.report, args.output))

"""Execute the declared four-density, seven-condition validation diagnostic."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.paired_genai import run
from models.collaborative.train_full import train as train_cf
from models.content.train_snapshot import fingerprint


def suite(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError('Use a new suite version; individual completed runs remain reusable evidence')
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    data = root/'data/processed'
    train = root/'data/splits/event-count-v1/train.csv'
    validation = root/'data/splits/event-count-v1/validation.csv'
    results = []
    for density in [10, 25, 50, 100]:
        variant = data/f'density-event-count-v1/density-{density}' if density != 100 else None
        cf_dir = output/f'cf-{density}' if variant else data/'cf-event-count-v1'
        if variant:
            print(f'Training CF at {density}% event density', flush=True)
            train_cf(variant/'train.csv', cf_dir, 1438558255147)
        print(f'Evaluating seven configurations at {density}% density', flush=True)
        destination = output/f'evaluation-{density}'
        run(train, validation, data/'content-event-count-v1', data/'content-genai-quality-v1',
            cf_dir, data/'validation-tuning-v1', destination, variant)
        report = json.loads((destination/'report.json').read_text())
        results.append({'density_percent': density, 'report_sha256': fingerprint(destination/'report.json'),
                        'summaries': report['summaries'], 'original_cohort_summaries': report['original_cohort_summaries'],
                        'cohort_migration': report['cohort_migration'], 'exposure': report['exposure'],
                        'candidate_universe_size': report['candidate_universe_size'], 'paired': report['paired']})
    result = {'status': 'development_density_suite_not_final_hypothesis_evidence',
              'densities': results, 'source_sha256': fingerprint(__file__),
              'limitations': ['200 original-stratified validation users, not population-representative final testing',
                             'Density changes observed history, cohorts and novel-target counts',
                             'Settings fixed from full-density tuning; no density-specific retuning',
                             'GenAI covers only 21 of 411732 catalogue rows']}
    (output/'report.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    return [{ 'density': r['density_percent'], 'exposure': r['exposure']} for r in results]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(suite(parser.parse_args().output), indent=2))

"""Freeze a previously analyzed selection before any generation requests."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.enrichment import validate_catalogue
from models.content.train_snapshot import fingerprint


def freeze(analysis_dir, catalogue, output, design='training_profile_support', size=128):
    analysis_dir, catalogue, output = Path(analysis_dir), Path(catalogue), Path(output)
    if output.exists():
        raise FileExistsError('Never overwrite a frozen sample')
    report = json.loads((analysis_dir/'report.json').read_text())
    selections_path = analysis_dir/'selections.json'
    if fingerprint(selections_path) != report['selections_sha256']:
        raise ValueError('Selection fingerprint mismatch')
    expected = [v for k, v in report['inputs_sha256'].items()
                if Path(k.replace('\\', '/')).name == 'catalogue.jsonl']
    if expected != [fingerprint(catalogue)]:
        raise ValueError('Catalogue differs from analyzed source')
    choices = [r for r in report['comparisons'] if r['design'] == design and r['size'] == size]
    if len(choices) != 1 or choices[0]['oversized_records_not_sendable']:
        raise ValueError('Require one analyzed, sendable design')
    ids = json.loads(selections_path.read_text())[f'{design}-{size}']
    if len(ids) != size or len(set(ids)) != size:
        raise ValueError('Invalid selected population')
    selected_ids = set(ids)
    rows = []
    with catalogue.open(encoding='utf-8') as stream:
        for line in stream:
            record = json.loads(line)
            if record['itemid'] in selected_ids:
                rows.append(validate_catalogue(record))
    if len(rows) != size or len({r['as_of_ms'] for r in rows}) != 1:
        raise ValueError('Missing items or inconsistent cutoff')
    if any(r['properties'].get('available') == '0' for r in rows):
        raise ValueError('Selected unavailable item')
    rows.sort(key=lambda r: r['itemid'])
    output.mkdir(parents=True)
    source = output/'catalogue.jsonl'
    source.write_text(''.join(json.dumps(r, sort_keys=True)+'\n' for r in rows), encoding='utf-8')
    manifest = {'design': design, 'size': size, 'seed': report['seed'],
                'cutoff_ms': rows[0]['as_of_ms'], 'eligible_population': report['eligible_catalogue_items'],
                'itemids': [r['itemid'] for r in rows], 'source_sha256': fingerprint(catalogue),
                'sample_sha256': fingerprint(source), 'analysis_sha256': fingerprint(analysis_dir/'report.json'),
                'sample_availability': dict(Counter(r['properties'].get('available', 'unknown') for r in rows)),
                'selection_evidence': choices[0],
                'limitations': ['Targeted development sample, not representative catalogue quality evidence',
                               'No validation/test outcomes or assessment membership used to choose items',
                               'No replacements for failed or rejected generations',
                               'Generation and source reviews do not establish ranking effectiveness']}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['analysis-dir', 'catalogue', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--size', type=int, default=128)
    parser.add_argument('--design', default='training_profile_support')
    result = freeze(**vars(parser.parse_args()))
    print(json.dumps({k: v for k, v in result.items() if k != 'itemids'}, indent=2))

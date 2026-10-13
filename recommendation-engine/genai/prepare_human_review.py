"""Prepare local review packets without revealing assistant screening decisions."""
import argparse
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.enrichment import sha
from genai.quality_report import report
from models.content.train_snapshot import fingerprint


RUBRIC = {
    'supported_assertions': 'Count independently assessable factual assertions supported by the source.',
    'unsupported_assertions': 'Count assertions contradicted by or absent from the source; cite each in notes.',
    'unassessable_assertions': 'Count assertions whose truth cannot be judged from anonymous codes.',
    'clarity_1_to_5': '1 incomprehensible, 2 difficult, 3 understandable, 4 clear, 5 very clear.',
    'usefulness_1_to_5': '1 no help understanding the item, 2 little, 3 some, 4 substantial, 5 very useful.',
    'unsupported_claim_severity': 'none, minor, major, or unassessable; explain in notes.',
    'notes': 'Record assertion boundaries and evidence; do not guess what anonymous codes mean.',
}


def prepare(sample, cache, output, seed=42):
    sample, cache, output = Path(sample), Path(cache), Path(output)
    if output.exists():
        raise FileExistsError('Use a new packet version; never overwrite ratings')
    evidence = report(sample, cache)
    if evidence['status'] != 'complete_sample':
        raise ValueError('Finish the declared sample before preparing its review packet')
    successes = [row for row in evidence['attempts'] if row['status'] == 'generated_pending_review']
    random.Random(seed).shuffle(successes)
    cases, mapping = [], []
    for number, row in enumerate(successes, 1):
        result = json.loads((cache/(row['cache_key']+'.json')).read_text())
        case_id = f'Q{number:03d}'
        cases.append({'case_id': case_id,
                      'historical_source_properties': result['identity']['catalogue']['properties'],
                      'generated_output': result['output'],
                      'ratings': {name: None for name in RUBRIC}})
        mapping.append({'case_id': case_id, 'cache_key': row['cache_key'],
                        'output_sha256': sha(result['output'])})
    packet = {'status': 'unrated', 'reviewer_code': None, 'review_date': None,
              'rubric': RUBRIC,
              'instructions': [
                  'Work independently before discussing disagreements; do not inspect assistant reviews.',
                  'Sources describe a historical snapshot, not current retail availability.',
                  'Separate factual support from clarity and usefulness; a list of correct codes may be unhelpful.',
                  'Mark unassessable claims explicitly. Leave missing ratings null, never impute them.',
                  'This packet hides assistant decisions, not the fact that the text is AI generated.',
              ], 'cases': cases}
    output.mkdir(parents=True)
    (output/'reviewer-template.json').write_text(json.dumps(packet, indent=2), encoding='utf-8')
    (output/'coordinator-key.json').write_text(json.dumps(mapping, indent=2), encoding='utf-8')
    manifest = {'status': 'prepared_no_human_ratings_collected', 'seed': seed,
                'sample_manifest_sha256': fingerprint(sample/'manifest.json'),
                'successful_outputs_included': len(cases),
                'failed_attempts_not_rateable': evidence['failed_or_rejected'],
                'selection': 'Every schema-valid output, independent of assistant approval',
                'template_sha256': fingerprint(output/'reviewer-template.json'),
                'key_sha256': fingerprint(output/'coordinator-key.json'),
                'source_sha256': fingerprint(__file__)}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['sample', 'cache', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    print(json.dumps(prepare(**vars(parser.parse_args())), indent=2))

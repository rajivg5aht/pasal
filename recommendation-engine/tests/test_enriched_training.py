import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np
from scipy.sparse import load_npz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.enrichment import cache_lock, cached_enrichment, sha
from genai.free_provider import GroqFreeProvider
from genai.sample_catalogue import sample_catalogue
from models.content.train_snapshot import train as train_base
from models.content.train_enriched import train
from models.engine import load_artifact


class EnrichedTrainingTests(unittest.TestCase):
    def test_only_reviewed_matching_row_changes_and_untreated_vectors_are_exact(self):
        # Mocked outputs stay in a temporary fixture; never research evidence.
        with TemporaryDirectory() as directory:
            root = Path(directory)
            records = [{'itemid': i, 'as_of_ms': 100, 'source_sha256': 'a'*64,
                        'properties': {'categoryid': '209', 'available': '1'}} for i in range(4)]
            source = root/'catalogue.jsonl'
            source.write_text(''.join(json.dumps(r)+'\n' for r in records))
            train_base(source, root/'base', 100)
            sample_catalogue(source, root/'sample', 4)
            provider = GroqFreeProvider()
            output = {'description': 'Historical category 209.', 'source_properties': ['categoryid'],
                      'limitations': 'Anonymous codes only.'}
            with cache_lock(root/'cache'), patch.object(provider, 'generate', return_value=(output, {})):
                result, _ = cached_enrichment(records[0], provider, root/'cache')
            review = {'cache_key': result['cache_key'], 'output_sha256': sha(output),
                      'approved': True, 'reviewer': 'fixture', 'rationale': 'Fixture only'}
            reviews = root/'reviews.jsonl'
            reviews.write_text(json.dumps(review)+'\n')
            manifest = train(source, root/'base', root/'sample', root/'cache', reviews, root/'enriched')
            base = load_npz(root/'base/matrix.npz')
            enriched, items, _ = load_artifact(root/'enriched', 100)
            self.assertEqual(manifest['approved_items'], 1)
            self.assertEqual(manifest['rows'], 4)
            self.assertEqual((base[1:] != enriched[1:, :base.shape[1]]).nnz, 0)
            self.assertEqual(enriched[1:, base.shape[1]:].nnz, 0)
            self.assertGreater(enriched[0, base.shape[1]:].nnz, 0)
            np.testing.assert_allclose(np.asarray(enriched.multiply(enriched).sum(axis=1)).ravel(), 1, atol=1e-6)
            review['output_sha256'] = 'wrong'
            reviews.write_text(json.dumps(review)+'\n')
            with self.assertRaises(ValueError):
                train(source, root/'base', root/'sample', root/'cache', reviews, root/'bad')


if __name__ == '__main__':
    unittest.main()

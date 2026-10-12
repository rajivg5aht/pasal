import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.sample_catalogue import sample_catalogue
from genai.free_provider import FreeQuota, GroqFreeProvider, QuotaPaused


class SampleTests(unittest.TestCase):
    def test_reproducible_sample_excludes_unavailable_without_reading_events(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'catalogue.jsonl'
            rows = [{'itemid': i, 'as_of_ms': 100, 'source_sha256': 'a'*64,
                     'properties': {'available': '0' if i < 5 else '1', 'categoryid': str(i % 3)}}
                    for i in range(30)]
            source.write_text('\n'.join(json.dumps(r) for r in rows))
            first = sample_catalogue(source, root/'one', 8)
            second = sample_catalogue(source, root/'two', 8)
            self.assertEqual(first, second)
            self.assertEqual(first['eligible_population'], 25)
            self.assertEqual(len(set(first['itemids'])), 8)
            self.assertTrue(all(i >= 5 for i in first['itemids']))
            with self.assertRaises(FileExistsError):
                sample_catalogue(source, root/'one', 8)

    def test_daily_quota_never_requests_automatic_wait(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)/'quota.jsonl'
            path.write_text(json.dumps({'time': 950, 'tokens': 180000, 'cache_key': 'fixture'})+'\n')
            quota = FreeQuota(path, GroqFreeProvider(), clock=lambda: 1000)
            record = {'itemid': 1, 'as_of_ms': 100, 'source_sha256': 'a'*64,
                      'properties': {'categoryid': '9'}}
            with self.assertRaises(QuotaPaused) as error:
                quota(record, 'new')
            self.assertIsNone(error.exception.retry_after)
            self.assertEqual(len(path.read_text().splitlines()), 1)


if __name__ == '__main__':
    unittest.main()

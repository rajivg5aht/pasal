import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.enrichment import (OpenAIProvider, approved_text, cached_enrichment,
                              cache_lock, request_payload, sha, validate_catalogue, validate_generation)

RECORD = {"itemid": 7, "as_of_ms": 1234, "source_sha256": "a"*64,
          "properties": {"categoryid": "209", "790": "123 456"}}
OUTPUT = {"description": "Catalogue category 209. Semantic product details are unavailable.",
          "source_properties": ["categoryid"], "limitations": "Anonymized metadata."}


class FakeProvider:
    # Explicitly test-only: no generated research artifacts are made by this class.
    name = "fixture_only"
    model = "test_fixture"
    max_output_tokens = 800

    def __init__(self):
        self.calls = 0

    def generate(self, record):
        self.calls += 1
        return dict(OUTPUT), {"usage": {"input_tokens": 10, "output_tokens": 20}}


class EnrichmentTests(unittest.TestCase):
    def test_privacy_allowlist_rejects_user_data(self):
        for key in ["visitorid", "email", "history", "preferences"]:
            with self.assertRaises(ValueError):
                validate_catalogue({**RECORD, key: "private"})

    def test_request_contains_catalogue_only(self):
        payload = request_payload(RECORD, "configured-model", 800)
        self.assertFalse(payload["store"])
        self.assertEqual(json.loads(payload["input"]), {"properties": RECORD["properties"]})
        self.assertTrue(payload["text"]["format"]["strict"])

    def test_cache_reuses_same_generation(self):
        with TemporaryDirectory() as folder, cache_lock(folder):
            provider = FakeProvider()
            first, hit = cached_enrichment(RECORD, provider, folder)
            second, hit2 = cached_enrichment(RECORD, provider, folder)
            self.assertFalse(hit)
            self.assertTrue(hit2)
            self.assertEqual(provider.calls, 1)
            self.assertEqual(first, second)

    def test_source_changes_invalidate_cache(self):
        with TemporaryDirectory() as folder, cache_lock(folder):
            provider = FakeProvider()
            one, _ = cached_enrichment(RECORD, provider, folder)
            two, _ = cached_enrichment({**RECORD, "as_of_ms": 1235}, provider, folder)
            self.assertNotEqual(one["cache_key"], two["cache_key"])
            self.assertEqual(provider.calls, 2)

    def test_unsupported_numbers_or_citations_rejected(self):
        for changed in [{"description": "Costs 999 rupees"}, {"source_properties": ["brand"]}]:
            with self.assertRaises(ValueError):
                validate_generation({**OUTPUT, **changed}, RECORD)

    def test_unreviewed_text_never_enters_features(self):
        with TemporaryDirectory() as folder, cache_lock(folder):
            result, _ = cached_enrichment(RECORD, FakeProvider(), folder)
            with self.assertRaises(ValueError):
                approved_text(result, {})
            review = {"cache_key": result["cache_key"], "approved": True,
                      "output_sha256": sha(result["output"]), "reviewer": "test",
                      "rationale": "Fixture matches its source"}
            self.assertEqual(approved_text(result, review), OUTPUT["description"])
            review["output_sha256"] = "stale"
            with self.assertRaises(ValueError):
                approved_text(result, review)

    def test_budget_failure_prevents_dispatch(self):
        with TemporaryDirectory() as folder, cache_lock(folder):
            provider = FakeProvider()
            def deny(record, key):
                raise RuntimeError("No budget")
            with self.assertRaises(RuntimeError):
                cached_enrichment(RECORD, provider, folder, deny)
            self.assertEqual(provider.calls, 0)

    def test_real_provider_contract_and_refusal(self):
        response = Mock(status_code=200)
        response.json.return_value = {"status": "completed", "id": "response-fixture", "model": "configured-model",
            "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(OUTPUT)}]}],
            "usage": {"input_tokens": 10, "output_tokens": 20}}
        with patch.dict("os.environ", {"GENAI_API_KEY": "test-key"}), patch("genai.enrichment.requests.post", return_value=response) as post:
            generated, meta = OpenAIProvider("configured-model").generate(RECORD)
            self.assertEqual(generated, OUTPUT)
            self.assertEqual(meta["usage"]["output_tokens"], 20)
            self.assertEqual(post.call_args.args[0], "https://api.openai.com/v1/responses")
            response.json.return_value["output"][0]["content"] = [{"type": "refusal", "refusal": "No"}]
            with self.assertRaises(RuntimeError):
                OpenAIProvider("configured-model").generate(RECORD)


if __name__ == "__main__":
    unittest.main()

import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.free_provider import FreeQuota, GroqFreeProvider, ProviderFailure
from genai.explanations import explain
from genai.enrichment import cached_enrichment, cache_lock, sha

RECORD = {"itemid": 7, "as_of_ms": 1234, "source_sha256": "a" * 64,
          "properties": {"categoryid": "209"}}
OUTPUT = {"description": "Catalogue category 209.", "source_properties": ["categoryid"],
          "limitations": "Anonymous category."}


class FreeGenAITests(unittest.TestCase):
    def test_free_account_required_before_network(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture", "GROQ_ACCOUNT_TIER": "developer"}), patch("genai.free_provider.requests.post") as post:
            with self.assertRaises(ValueError):
                GroqFreeProvider().generate(RECORD)
            post.assert_not_called()

    def test_catalogue_only_and_usage_normalization(self):
        response = Mock(status_code=200, headers={"x-ratelimit-remaining-tokens": "100"})
        response.json.return_value = {"id": "fixture", "model": "openai/gpt-oss-20b",
            "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(OUTPUT)}}],
            "usage": {"prompt_tokens": 15, "completion_tokens": 20}}
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture", "GROQ_ACCOUNT_TIER": "free"}), patch("genai.free_provider.requests.post", return_value=response) as post:
            output, metadata = GroqFreeProvider().generate(RECORD)
        self.assertEqual(output, OUTPUT)
        self.assertEqual(metadata["usage"], {"input_tokens": 15, "output_tokens": 20})
        payload = post.call_args.kwargs["json"]
        self.assertEqual(json.loads(payload["messages"][1]["content"]), {"properties": RECORD["properties"]})
        self.assertFalse(post.call_args.kwargs["allow_redirects"])

    def test_rate_limit_stops_without_retry(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture", "GROQ_ACCOUNT_TIER": "free"}), patch("genai.free_provider.requests.post", return_value=Mock(status_code=429)) as post:
            with self.assertRaises(RuntimeError):
                GroqFreeProvider().generate(RECORD)
            self.assertEqual(post.call_count, 1)

    def test_incomplete_generation_retains_token_usage_without_accepting_text(self):
        response = Mock(status_code=200, headers={})
        response.json.return_value = {'id': 'fixture', 'model': 'openai/gpt-oss-20b',
            'choices': [{'finish_reason': 'length', 'message': {'content': '{unfinished'}}],
            'usage': {'prompt_tokens': 20, 'completion_tokens': 800}}
        with patch.dict(os.environ, {'GROQ_API_KEY': 'fixture', 'GROQ_ACCOUNT_TIER': 'free'}), patch('genai.free_provider.requests.post', return_value=response):
            with self.assertRaises(ProviderFailure) as failure:
                GroqFreeProvider().generate(RECORD)
        self.assertEqual(failure.exception.safe_metadata['usage']['output_tokens'], 800)
        self.assertNotIn('content', failure.exception.safe_metadata)

    def test_http_failure_records_only_allowlisted_code(self):
        response = Mock(status_code=400, headers={})
        response.json.return_value = {'error': {'code': 'json_validate_failed',
            'message': 'private response text', 'failed_generation': 'do not log'}}
        with patch.dict(os.environ, {'GROQ_API_KEY': 'fixture', 'GROQ_ACCOUNT_TIER': 'free'}), patch('genai.free_provider.requests.post', return_value=response):
            with self.assertRaises(ProviderFailure) as failure:
                GroqFreeProvider().generate(RECORD)
        self.assertEqual(failure.exception.safe_metadata, {'http_status': 400,
            'error_code': 'json_validate_failed', 'usage_unavailable': True})

    def test_quota_persists_and_resumes_after_window(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "quota.jsonl"
            provider = GroqFreeProvider()
            quota = FreeQuota(path, provider, clock=lambda: 1000)
            quota(RECORD, "one")
            quota(RECORD, "two")
            with self.assertRaises(RuntimeError):
                FreeQuota(path, provider, clock=lambda: 1000)(RECORD, "three")
            FreeQuota(path, provider, clock=lambda: 1061)(RECORD, "three")
            self.assertEqual(len(path.read_text().splitlines()), 3)

    def test_explanation_requires_review_and_matching_item(self):
        with TemporaryDirectory() as directory, cache_lock(directory):
            provider = GroqFreeProvider()
            with patch.object(provider, "generate", return_value=(OUTPUT, {})):
                result, _ = cached_enrichment(RECORD, provider, directory)
            review = {"cache_key": result["cache_key"], "output_sha256": sha(OUTPUT),
                      "approved": True, "reviewer": "fixture", "rationale": "fixture"}
            self.assertEqual(explain(7, "content", result, review)["description_source"], "reviewed_generative_api")
            with self.assertRaises(ValueError):
                explain(8, "content", result, review)
            self.assertEqual(explain(7, "content")["description_source"], "unavailable")
            with self.assertRaises(ValueError):
                explain(7, "content", {**result, "source_kind": "fixture"}, review)
            with self.assertRaises(ValueError):
                explain(7, "content", {**result, "cache_key": "tampered"}, review)


if __name__ == "__main__":
    unittest.main()

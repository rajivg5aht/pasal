import csv
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.build_enriched_features import export_features
from genai.enrichment import OpenAIProvider, cache_lock, cached_enrichment, sha


class GenAIFeatureTests(unittest.TestCase):
    def test_no_generation_fallback_is_identical_and_honestly_reported(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "catalogue.jsonl"
            record = {"itemid": 1, "as_of_ms": 100, "source_sha256": "a"*64,
                      "properties": {"categoryid": "209"}}
            source.write_text(json.dumps(record)+"\n")
            result = export_features(source, root / "no-cache", None, root / "out", "unconfigured")
            self.assertEqual(result["counts"]["approved_items"], 0)
            self.assertEqual(result["counts"]["fallback_items"], 1)
            self.assertEqual((root / "out/features_with_genai.csv").read_bytes(),
                             (root / "out/features_without_genai.csv").read_bytes())
            with self.assertRaises(FileExistsError):
                export_features(source, root / "no-cache", None, root / "out", "unconfigured")

    def test_reviewed_generation_is_added_only_to_matching_paired_row(self):
        # All provider calls are mocked and all artifacts are temporary fixtures.
        with TemporaryDirectory() as folder:
            root = Path(folder)
            record = {"itemid": 1, "as_of_ms": 100, "source_sha256": "a"*64,
                      "properties": {"categoryid": "209"}}
            source = root / "catalogue.jsonl"
            source.write_text(json.dumps(record)+"\n")
            output = {"description": "Catalogue category 209.", "source_properties": ["categoryid"],
                      "limitations": "Anonymized category."}
            provider = OpenAIProvider("fixture-model")
            with cache_lock(root / "cache"), patch.object(provider, "generate", return_value=(output, {"usage": {"input_tokens": 10, "output_tokens": 20}})):
                cached, _ = cached_enrichment(record, provider, root / "cache")
            review = {"cache_key": cached["cache_key"], "approved": True, "output_sha256": sha(output),
                      "reviewer": "fixture", "rationale": "Matches category ID"}
            reviews = root / "reviews.jsonl"
            reviews.write_text(json.dumps(review)+"\n")
            result = export_features(source, root / "cache", reviews, root / "out", "fixture-model")
            self.assertEqual(result["counts"]["approved_items"], 1)
            self.assertEqual(result["counts"]["output_tokens_reported"], 20)
            with (root / "out/features_with_genai.csv").open() as stream:
                enhanced = list(csv.DictReader(stream))
            with (root / "out/features_without_genai.csv").open() as stream:
                original = list(csv.DictReader(stream))
            self.assertEqual(enhanced[0]["itemid"], original[0]["itemid"])
            self.assertEqual(enhanced[0]["content"], original[0]["content"]+" "+output["description"])
            review["output_sha256"] = "incorrect"
            reviews.write_text(json.dumps(review)+"\n")
            with self.assertRaises(ValueError):
                export_features(source, root / "cache", reviews, root / "bad", "fixture-model")


if __name__ == "__main__":
    unittest.main()

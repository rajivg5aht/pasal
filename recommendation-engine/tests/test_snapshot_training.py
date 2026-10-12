import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models.content.train_snapshot import train


class SnapshotTrainingTests(unittest.TestCase):
    def test_cutoff_rejected_and_versioned_training_preserves_rows(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            catalogue = root / "catalogue.jsonl"
            records = [{"itemid": i, "as_of_ms": 100, "source_sha256": "a" * 64,
                        "properties": {"categoryid": "2", "available": str(i % 2)}} for i in range(4)]
            catalogue.write_text("\n".join(json.dumps(r) for r in records))
            with self.assertRaises(ValueError):
                train(catalogue, root / "wrong", 101)
            self.assertFalse((root / "wrong").exists())
            manifest = train(catalogue, root / "correct", 100)
            self.assertEqual(manifest["rows"], 4)
            self.assertEqual(manifest["zero_vector_rows"], 0)
            self.assertEqual(manifest["availability_counts"]["unavailable"], 2)
            with self.assertRaises(FileExistsError):
                train(catalogue, root / "correct", 100)


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models.content.train_snapshot import train
from evaluation.run_popularity_diagnostic import run


class TemporalDiagnosticTests(unittest.TestCase):
    def test_shared_availability_and_cold_start_across_three_models(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            catalogue = root / "catalogue.jsonl"
            catalogue.write_text("\n".join(json.dumps({"itemid": i, "as_of_ms": 100,
                "source_sha256": "a" * 64, "properties": {"categoryid": "9", "available": "0" if i == 2 else "1"}})
                for i in [1, 2, 3, 4]))
            train(catalogue, root / "content", 100)
            columns = ["timestamp", "visitorid", "itemid", "event"]
            pd.DataFrame([(1, 1, 1, "view"), (2, 3, 2, "transaction"), (3, 4, 3, "view")], columns=columns).to_csv(root / "train.csv", index=False)
            pd.DataFrame([(100, 1, 3, "view"), (101, 2, 4, "view")], columns=columns).to_csv(root / "val.csv", index=False)
            summaries = run(root / "train.csv", root / "val.csv", root / "run", content_dir=root / "content")
            self.assertEqual(len([s for s in summaries if s["cohort"] == "all"]), 3)
            rows = [json.loads(line) for line in (root / "run/per_user.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 6)
            for row in rows:
                self.assertNotIn(2, row["recommendations"])
                self.assertIsNone(row["failure"])
            cold = next(r for r in rows if r["visitorid"] == 2 and r["model"] == "tfidf")
            self.assertEqual(cold["recommendations"], [])
            self.assertEqual(cold["cohort"], "0")


if __name__ == "__main__":
    unittest.main()

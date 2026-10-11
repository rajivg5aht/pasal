import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preprocessing.build_metadata_snapshot import build, ingest, initialize


class SnapshotTests(unittest.TestCase):
    def test_latest_only_and_future_excluded_across_chunks(self):
        with sqlite3.connect(":memory:") as db:
            initialize(db)
            for rows in [[(20,1,"categoryid","20"), (10,1,"categoryid","10")],
                         [(30,1,"categoryid","30"), (40,2,"categoryid","40")]]:
                ingest(db, pd.DataFrame(rows, columns=["timestamp","itemid","property","value"]), 30, "fixture")
            self.assertEqual(db.execute("SELECT itemid,value,timestamp FROM facts").fetchall(), [(1,"20",20)])

    def test_conflicting_latest_values_are_flagged_until_newer_fact(self):
        with sqlite3.connect(":memory:") as db:
            initialize(db)
            frame = pd.DataFrame([(10,1,"categoryid","A"), (10,1,"categoryid","B")],
                                 columns=["timestamp","itemid","property","value"])
            ingest(db, frame, 100, "fixture")
            self.assertEqual(db.execute("SELECT ambiguous FROM facts").fetchone()[0], 1)
            newer = pd.DataFrame([(11,1,"categoryid","C")], columns=frame.columns)
            ingest(db, newer, 100, "fixture")
            self.assertEqual(db.execute("SELECT value,ambiguous FROM facts").fetchone(), ("C",0))

    def test_build_records_provenance_and_refuses_overwrite(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "properties.csv"
            pd.DataFrame([(1,4,"categoryid","209"),(9,4,"categoryid","999"),(1,5,"categoryid","210")],
                columns=["timestamp","itemid","property","value"]).to_csv(path,index=False)
            result = build([path], 5, root / "out", chunksize=1)
            records = [json.loads(x) for x in (root / "out/catalogue.jsonl").read_text().splitlines()]
            self.assertEqual(result["exported_items"], 2)
            self.assertEqual(records[0]["properties"]["categoryid"], "209")
            self.assertEqual(len(records[0]["source_sha256"]), 64)
            with self.assertRaises(FileExistsError):
                build([path], 5, root / "out")


if __name__ == "__main__":
    unittest.main()

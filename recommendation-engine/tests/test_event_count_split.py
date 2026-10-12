from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preprocessing.build_event_count_development import boundaries, build


class SplitTests(unittest.TestCase):
    def test_counts_and_ties_preserve_strict_time_separation(self):
        self.assertEqual(boundaries(list(range(100)))["effective_counts"], [70, 15, 15])
        result = boundaries(list(range(69)) + [69] * 3 + list(range(72, 100)))
        self.assertEqual(result["effective_counts"], [69, 16, 15])

    def test_development_build_preserves_originals_and_exposure(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            events = pd.DataFrame({"timestamp": range(100), "visitorid": [1] * 100,
                                   "itemid": range(100), "event": ["view"] * 100})
            events.to_csv(root / "raw.csv", index=False)
            events.iloc[:74].iloc[::-1].to_csv(root / "train.csv", index=False)
            events.iloc[74:87].iloc[::-1].to_csv(root / "val.csv", index=False)
            before = (root / "train.csv").read_bytes()
            result = build(root / "raw.csv", root / "train.csv", root / "val.csv", root / "new")
            self.assertEqual(result["previously_exposed_test_events"], 2)
            self.assertEqual(len(pd.read_csv(root / "new/train.csv")), 70)
            self.assertTrue(pd.read_csv(root / "new/validation.csv").timestamp.is_monotonic_increasing)
            self.assertFalse((root / "new/test.csv").exists())
            self.assertEqual((root / "train.csv").read_bytes(), before)
            with self.assertRaises(FileExistsError):
                build(root / "raw.csv", root / "train.csv", root / "val.csv", root / "new")


if __name__ == "__main__":
    unittest.main()

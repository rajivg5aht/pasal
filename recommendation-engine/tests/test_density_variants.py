import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.build_density_variants import build


class DensityTests(unittest.TestCase):
    def test_nested_subsamples_preserve_tied_event_order_and_original(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'train.csv'
            data = pd.DataFrame({'timestamp': [i//2 for i in range(100)],
                                 'visitorid': list(range(100)), 'itemid': [7]*100, 'event': ['view']*100})
            data.to_csv(source, index=False)
            original = source.read_bytes()
            build(source, root/'density', 100)
            sets = []
            for percentage in [10, 25, 50]:
                folder = root/'density'/f'density-{percentage}'
                indexes = np.load(folder/'source_rows.npy')
                subset = pd.read_csv(folder/'train.csv')
                self.assertEqual(len(subset), percentage)
                pd.testing.assert_frame_equal(subset, data.iloc[indexes].reset_index(drop=True))
                sets.append(set(indexes))
            self.assertTrue(sets[0] < sets[1] < sets[2])
            self.assertEqual(source.read_bytes(), original)
            with self.assertRaises(FileExistsError):
                build(source, root/'density', 100)


if __name__ == '__main__':
    unittest.main()

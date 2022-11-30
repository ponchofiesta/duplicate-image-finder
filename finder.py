import os
import imageio.v3 as iio
import numpy as np
import tqdm
from multiprocessing.pool import ThreadPool

dir = r"C:\Users\poncho\Desktop\Duplikate"


class DuplicateFinder:
    _colors = ("red", "green", "blue")

    def log(self, msg):
        if self._progress:
            print(msg)

    def process(self, imap, total):
        if self._progress:
            return list(tqdm.tqdm(imap, total=total))
        else:
            return imap

    def find(self, path, threshold, progress=False):
        self._progress = progress

        # Prepare file paths
        abs_paths = [os.path.join(path, file) for file in os.listdir(path)]

        # Get all histograms
        self.log("Creating histograms...")
        with ThreadPool() as pool:
            histograms = self.process(pool.imap_unordered(self.get_histogram, abs_paths), len(abs_paths))
        
        # Prepare diffs
        pairs = []
        for i, a in enumerate(histograms):
            for b in histograms[i+1:]:
                pair = {
                    "a": a,
                    "b": b,
                }
                pairs.append(pair)

        # Get all diffs
        self.log("Comparing files...")
        with ThreadPool() as pool:
            diffs = self.process(pool.imap_unordered(self.get_diff, pairs), len(pairs))

        # Apply threshold
        diffs = [diff for diff in diffs if diff["diff"] < threshold]

        return diffs
        

    def get_histogram(self, path):
        image = iio.imread(uri=path)
        color_histogram = {}
        for channel_id, color in enumerate(self._colors):
            histogram, bin_edges = np.histogram(image[:, :, channel_id], bins=256, range=(0, 256))
            color_histogram[color] = histogram
        return {
            "path": path,
            "histogram": color_histogram,
        }

    def get_diff(self, pair):
        diff = 0
        for color in pair["a"]["histogram"]:
            diff += np.sum(np.absolute(pair["a"]["histogram"][color] - pair["b"]["histogram"][color]))
        return {
            "a": pair["a"],
            "b": pair["b"],
            "diff": diff,
        }


finder = DuplicateFinder()
diffs = finder.find(dir, 10000000, True)
for d in diffs:
    print(d["a"]["path"], d["b"]["path"], d["diff"])

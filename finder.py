import os
from multiprocessing.pool import ThreadPool

import imageio.v3 as iio
import numpy as np
import tqdm


class DuplicateFinder:
    _colors = ("red", "green", "blue")

    def log(self, msg):
        if self._progress:
            print(msg)

    def process(self, imap, total):
        if self._progress:
            return list(tqdm.tqdm(imap, total=total))
        return imap

    def find(self, path, threshold=10_000_000, progress=False):
        self._progress = progress

        # Prepare file paths
        abs_paths = [os.path.join(path, file) for file in os.listdir(path)]

        # Get all histograms
        self.log("Creating histograms...")
        with ThreadPool() as pool:
            histograms = self.process(pool.imap_unordered(self.get_histogram, abs_paths), len(abs_paths), )

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

    def get_groups(self, pairs):

        def in_group(a, b, group):
            for item in group:
                if a["path"] == item["path"]:
                    group.append(b)
                    return True
                elif b["path"] == item["path"]:
                    group.append(a)
                    return True
            return False

        groups = []
        for pair in pairs:
            found = False
            for group in groups:
                if in_group(pair["a"], pair["b"], group):
                    found = True
            if not found:
                groups.append([pair["a"], pair["b"]])

        return groups


if __name__ == "__main__":
    #dir = r"C:\Users\poncho\Desktop\Duplikate"
    dir = r"Duplikate"
    finder = DuplicateFinder()
    pairs = finder.find(dir, 10000000, True)

    # for d in pairs:
    #     print(d["a"]["path"], d["b"]["path"], d["diff"])

    groups = finder.get_groups(pairs)
    for group in groups:
        print([item["path"] for item in group])

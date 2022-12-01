import os
from multiprocessing.pool import ThreadPool
import re

import imageio.v3 as iio
import numpy as np
import tqdm


class DuplicateFinder:
    _colors = ("red", "green", "blue")

    def _log(self, msg):
        if self._progress:
            print(msg)

    def _process(self, imap, total):
        if self._progress:
            return list(tqdm.tqdm(imap, total=total))
        return imap

    def find(self, path, threshold=10_000_000, progress=False):
        self._progress = progress

        # Prepare file paths
        abs_paths = [os.path.join(path, file) for file in os.listdir(path) if re.match('.*\.(jpe?g)$', file, re.I) is not None]

        # Get all histograms
        self._log("Creating histograms...")
        with ThreadPool() as pool:
            histograms = self._process(pool.imap_unordered(self.get_histogram, abs_paths), len(abs_paths))
        histograms = [histogram for histogram in histograms if histogram is not None]

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
        self._log("Comparing files...")
        with ThreadPool() as pool:
            diffs = self._process(pool.imap_unordered(self.get_diff, pairs), len(pairs))

        # Apply threshold
        diffs = [diff for diff in diffs if diff["diff"] < threshold]

        return diffs

    def get_histogram(self, path):
        try:
            image = iio.imread(uri=path)
        except Exception as e:
            print(f"WARNING: Cannot open {path}: {e}")
            return None
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

        def contains(list, filter):
            for x in list:
                if filter(x):
                    return True
            return False

        def in_group(a, b, group):
            has_a = contains(group, lambda x: x["path"] == a["path"])
            has_b = contains(group, lambda x: x["path"] == b["path"])
            if has_a:
                if not has_b:
                    group.append(b)
                return True
            elif has_b:
                if not has_a:
                    group.append(b)
                return True
            return False

        def in_groups(a, b, groups):
            found = False
            for group in groups:
                if in_group(a, b, group):
                    found = True
                    break

            if not found:
                groups.append([a, b])

        groups = []
        for pair in pairs:
            in_groups(pair["a"], pair["b"], groups)

        return groups

import re
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Any, Callable, List

import imageio.v3 as iio
import numpy as np

ProgressHandler = Callable[[int, str], Any]


class DuplicateFinder:
    _colors = ("red", "green", "blue")

    def __init__(self) -> None:
        self.cancel = False

    @property
    def cancel(self) -> bool:
        return self._cancel

    @cancel.setter
    def cancel(self, value: bool):
        self._cancel = value

    def find(self, path: str, threshold: int = 10_000_000, progress_handler: ProgressHandler = None):
        self._progress_handler = progress_handler

        # Get all file paths
        def get_paths(path: Path) -> List[Path]:
            for entry in path.rglob('*'):
                if self.cancel:
                    return []

                if entry.is_file():
                    if re.match('.*\.(jpe?g)$', entry.name, re.I) is not None:
                        abs_paths.append(entry.absolute())
                elif entry.is_dir():
                    get_paths(entry)

        abs_paths = []
        get_paths(Path(path))

        # Get all histograms
        status = "Creating histograms..."
        self._progress_handler(0, f"{status} (1/2)")

        with ThreadPool() as pool:
            total = len(abs_paths)
            histograms = []
            for i, histogram in enumerate(pool.imap_unordered(self.get_histogram, abs_paths)):
                if self.cancel:
                    pool.terminate()
                    return []
                self._progress_handler(i / total * 100, f"{status} (1/2)")
                if histogram is not None:
                    histograms.append(histogram)

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
        status = "Comparing files..."
        self._progress_handler(0, f"{status} (2/2)")
        diffs = []
        with ThreadPool() as pool:
            total = len(pairs)
            for i, diff in enumerate(pool.imap_unordered(self.get_diff, pairs)):
                if self.cancel:
                    pool.terminate()
                    return []
                self._progress_handler(i / total * 100, f"{status} (2/2)")
                if diff["diff"] < threshold:
                    diffs.append(diff)

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

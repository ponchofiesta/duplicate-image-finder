import re
from dataclasses import dataclass
from enum import Enum
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Any, Callable, Optional

import imageio.v3 as iio
import numpy as np

ProgressHandler = Callable[[int, str], Any]


class Color(Enum):
    red = 0
    green = 1
    blue = 2


Histogram = np.ndarray
RgbHistogram = dict[Color, Histogram]


@dataclass
class ImageInfo:
    path: Path
    histogram: RgbHistogram

    def __sub__(self, other):
        if not isinstance(other, ImageInfo):
            return self - other
        diff: int = 0
        for color in self.histogram:
            diff += np.sum(np.absolute(self.histogram[color] - other.histogram[color]))
        return diff

    def __hash__(self):
        return hash(self.path)


@dataclass
class Pair:
    a: ImageInfo
    b: ImageInfo
    diff: Optional[int]


ImageInfoGroup = set[ImageInfo]


class DuplicateFinder:
    def __init__(self) -> None:
        self.cancel = False

    @property
    def cancel(self) -> bool:
        return self._cancel

    @cancel.setter
    def cancel(self, value: bool):
        self._cancel = value

    def find(self, path: str, threshold: int = 10_000_000, progress_handler: Optional[ProgressHandler] = None) -> list[ImageInfoGroup]:

        if progress_handler is not None:
            self._progress_handler = progress_handler

        # Get all file paths
        def get_paths(path: Path) -> None:
            for entry in path.rglob('*'):
                if self.cancel:
                    return

                if entry.is_file():
                    if re.match(r'.*\.(jpe?g)$', entry.name, re.I) is not None:
                        abs_paths.append(entry)
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
                self._progress_handler(int(i / total * 100), f"{status} (1/2)")
                if histogram is not None:
                    histograms.append(histogram)

        # Prepare diffs
        pairs = []
        for i, a in enumerate(histograms):
            for b in histograms[i+1:]:
                pair = Pair(a=a, b=b, diff=None)
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
                self._progress_handler(int(i / total * 100), f"{status} (2/2)")
                if diff.diff is not None and diff.diff < threshold:
                    diffs.append(diff)

        groups = self.get_groups(diffs)

        return groups

    def get_histogram(self, path: Path) -> Optional[ImageInfo]:
        try:
            image = iio.imread(uri=path.absolute())
        except Exception as e:
            print(f"WARNING: Cannot open {path}: {e}")
            return None
        color_histogram: RgbHistogram = {}
        for color in list(Color):
            histogram, bin_edges = np.histogram(image[:, :, color.value], bins=256, range=(0, 256))
            color_histogram[color] = histogram
        return ImageInfo(path=path, histogram=color_histogram)

    def get_diff(self, pair: Pair) -> Pair:
        pair.diff = pair.a - pair.b
        return pair

    def get_groups(self, pairs: list[Pair]) -> list[ImageInfoGroup]:
        groups: list[ImageInfoGroup] = []
        for pair in pairs:
            pair_in_groups = []

            # Search items in all groups
            for i, group in enumerate(groups):
                if pair.a in group or pair.b in group:
                    pair_in_groups.append(i)

            # If matching items were found in multiple groups, merge those groups
            if len(pair_in_groups) > 1:
                for group_id in reversed(pair_in_groups[1:]):
                    groups[pair_in_groups[0]].update(groups[group_id])
                    del groups[group_id]

            # Add items to the groups
            if len(pair_in_groups) > 0:
                groups[pair_in_groups[0]].update([pair.a, pair.b])
            else:
                groups.append(set([pair.a, pair.b]))

        return groups

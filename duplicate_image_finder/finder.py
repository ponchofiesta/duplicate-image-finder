import re
from dataclasses import dataclass, field
from enum import Enum
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Any, Callable, Literal, Optional

import imageio.v3 as iio
import image_utils
import numpy as np
from numba import jit

ProgressHandler = Callable[[int, str], Any]


class Color(Enum):
    red = 0
    green = 1
    blue = 2


Histogram = np.ndarray
RgbHistogram = dict[Color | int, Histogram]


@dataclass
class ImageInfo:
    path: Path
    error: Optional[Exception] = field(default=None)
    histogram: Optional[RgbHistogram] = field(default=None)
    checked: bool = field(init=False, default=True)

    def __sub__(self, other):
        if not isinstance(other, ImageInfo):
            return self - other
        diff: int = 0
        if self.histogram is None or other.histogram is None:
            raise TypeError("histogram must be not None")
        for (color, _) in enumerate(self.histogram):
            for (a, b) in zip(self.histogram[color], other.histogram[color]):
                diff += abs(a - b)
        return diff

    def __hash__(self):
        return hash(self.path)


@dataclass
class Pair:
    a: ImageInfo
    b: ImageInfo
    diff: Optional[int]


ImageInfoGroup = dict[ImageInfo, Literal[None]]


class DuplicateFinder:
    """Get image infos and compare them to find similar images"""

    # HISTOGRAM_MAX = 1000

    def __init__(self) -> None:
        self.cancel = False

    @property
    def cancel(self) -> bool:
        """Cancel processing"""
        return self._cancel

    @cancel.setter
    def cancel(self, value: bool):
        self._cancel = value

    def find(self, path: str, threshold: int = 10_000_000, progress_handler: Optional[ProgressHandler] = None) -> tuple[list[ImageInfoGroup], list[Path]]:
        """Find duplicate images"""
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
            failed = []
            for i, histogram in enumerate(pool.imap_unordered(self.get_histogram, abs_paths)):
                if self.cancel:
                    pool.terminate()
                    return ([], [])
                self._progress_handler(int(i / total * 100), f"{status} (1/2)")
                if histogram.error is not None:
                    failed.append(histogram)
                elif histogram.histogram is not None:
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
                    return ([], [])
                self._progress_handler(int(i / total * 100), f"{status} (2/2)")
                if diff.diff is not None and diff.diff < threshold:
                    diffs.append(diff)

        groups = self.get_groups(diffs)

        # Set checked on first image of each group
        for group in groups:
            item = next(iter(group.keys()))
            item.checked = False

        return (groups, failed)
    
    def get_histogram(self, path: Path) -> ImageInfo:
        """Get color histgram of each channel of an image"""
        try:
            color_histogram: RgbHistogram = image_utils.get_histograms_from_image(str(path.absolute()))
        except Exception as e:
            return ImageInfo(path=path, error=e)
        return ImageInfo(path=path, histogram=color_histogram)
    
    def get_diff(self, pair: Pair) -> Pair:
        """Calculate difference between two images"""
        pair.diff = pair.a - pair.b
        return pair

    def get_groups(self, pairs: list[Pair]) -> list[ImageInfoGroup]:
        """Create groups of similar images"""
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
                groups[pair_in_groups[0]].update([(pair.a, None), (pair.b, None)])
            else:
                groups.append(dict.fromkeys([pair.a, pair.b]))

        return groups


@jit(nopython=True)
def get_bin_edges(a, bins):
    bin_edges = np.zeros((bins+1,), dtype=np.float64)
    a_min = a.min()
    a_max = a.max()
    delta = (a_max - a_min) / bins
    for i in range(bin_edges.shape[0]):
        bin_edges[i] = a_min + i * delta

    bin_edges[-1] = a_max  # Avoid roundoff error on last point
    return bin_edges


@jit(nopython=True)
def compute_bin(x, bin_edges):
    # assuming uniform bins for now
    n = bin_edges.shape[0] - 1
    a_min = bin_edges[0]
    a_max = bin_edges[-1]

    # special case to mirror NumPy behavior for last bin
    if x == a_max:
        return n - 1  # a_max always in last bin

    bin = int(n * (x - a_min) / (a_max - a_min))

    if bin < 0 or bin >= n:
        return None
    else:
        return bin


@jit(nopython=True)
def numba_histogram(a, bins):
    hist = np.zeros((bins,), dtype=np.intp)
    bin_edges = get_bin_edges(a, bins)

    for x in a.flat:
        bin = compute_bin(x, bin_edges)
        if bin is not None:
            hist[int(bin)] += 1

    return hist, bin_edges

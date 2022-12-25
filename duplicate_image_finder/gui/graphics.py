from pathlib import Path
from typing import Optional

from PIL import ExifTags, Image
from PIL.ImageTk import PhotoImage


class Cache:
    def __init__(self, max_len: int = 20) -> None:
        self._cache = {}
        self._max_len = max_len

    def add(self, key, value):
        self._cache[key] = value
        if len(self._cache) > self._max_len:
            self._cache.pop(next(iter(self._cache)))

    def get(self, key):
        return self._cache.get(key)


image_cache: Optional[Cache] = None


def load_image(path: Path, width: Optional[int] = None, height: Optional[int] = None) -> PhotoImage:
    if width is not None and height is None:
        height = width
    elif width is None and height is not None:
        width = height

    global image_cache
    if image_cache is None:
        image_cache = Cache()
    cache_key = f'{path};{width}x{height}'

    photo_image = image_cache.get(cache_key)
    if photo_image is not None:
        return photo_image

    image = Image.open(path)
    if width is not None and height is not None:
        image.thumbnail((width, height), Image.BICUBIC)

    # Rotate image according to EXIF data
    orientation = 0
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break
    exif = image.getexif()
    if exif[orientation] == 3:
        image = image.rotate(180, expand=True)
    elif exif[orientation] == 6:
        image = image.rotate(270, expand=True)
    elif exif[orientation] == 8:
        image = image.rotate(90, expand=True)

    photo_image = PhotoImage(image)
    image_cache.add(cache_key, photo_image)
    return photo_image

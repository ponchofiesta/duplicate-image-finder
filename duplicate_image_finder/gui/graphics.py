from pathlib import Path
from typing import Optional
from PIL import ExifTags, Image
from PIL.ImageTk import PhotoImage


def load_image(path: Path, width: Optional[int] = None, height: Optional[int] = None) -> PhotoImage:
    if width is not None and height is None:
        height = width
    elif width is None and height is not None:
        width = height

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
    return photo_image

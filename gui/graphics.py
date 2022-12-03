from PIL import ExifTags, Image
from PIL.ImageTk import PhotoImage


def load_image(path: str, width: int = None, height: int = None) -> PhotoImage:
    if width is not None and height is None:
        height = width
    elif width is None and height is not None:
        width = height

    image = Image.open(path)
    if width is not None:
        image.thumbnail((width, height), Image.BICUBIC)

    # Rotate image according to EXIF data
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break
    exif = image._getexif()
    if exif[orientation] == 3:
        image = image.rotate(180, expand=True)
    elif exif[orientation] == 6:
        image = image.rotate(270, expand=True)
    elif exif[orientation] == 8:
        image = image.rotate(90, expand=True)

    photo_image = PhotoImage(image)
    return photo_image

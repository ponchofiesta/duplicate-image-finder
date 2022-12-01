import pathlib
from tkinter import IntVar
from typing import List

import pygubu
from idlelib.tooltip import Hovertip
from PIL import ExifTags
from PIL import Image as PILImage
from PIL import ImageTk

VIEWS_PATH = pathlib.Path(__file__).parent / "views"


class Image:
    def __init__(self, path: str, checked=False, master=None) -> None:
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(VIEWS_PATH)
        builder.add_from_file(VIEWS_PATH / "image.ui")
        self.mainwindow = builder.get_object('imageFrame', master)
        self._label = builder.get_object('imageLabel')
        self._checkbox = builder.get_object('imageCheckbox')

        self.path = path
        self.checked = checked

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

        image = PILImage.open(self._path)
        image.thumbnail((128, 128), PILImage.BICUBIC)

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

        self._image = ImageTk.PhotoImage(image)

        self._label.configure(image=self._image)
        self._label.image = self._image
        tooltip = Hovertip(self._label, self.path)

    @property
    def checked(self):
        return self._checked.get() == 1

    @checked.setter
    def checked(self, value):
        self._checked = IntVar(value=0)
        if value:
            self._checked = IntVar(value=1)
        self._checkbox.configure(variable=self._checked)
        self._checkbox.checked = self._checked


class ImageGroup:
    def __init__(self, image_paths: List[str], title="", master=None) -> None:

        self._images: List[Image] = []

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(VIEWS_PATH)
        builder.add_from_file(VIEWS_PATH / "image_group.ui")
        self.mainwindow = builder.get_object('imageGroup', master)
        self._label = builder.get_object('imageGroupLabel')
        self._image_list = builder.get_object('imageGroupList')

        self.title = title
        self.paths = image_paths

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self._label.configure(text=self._title)

    @property
    def paths(self):
        return self._image_paths

    @paths.setter
    def paths(self, value):
        self._image_paths = value
        self.load_images()

    @property
    def images(self):
        return self._images

    def load_images(self):
        self._images = []
        for i, path in enumerate(self._image_paths):
            image = Image(path, checked=True, master=self._image_list)
            if i == 0:
                image.checked = False
            self._images.append(image)

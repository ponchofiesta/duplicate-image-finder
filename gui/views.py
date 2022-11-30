import pathlib
from tkinter import IntVar, ttk
import tkinter as tk
from typing import List
import pygubu
from PIL import ImageTk, Image as PILImage, ExifTags


PROJECT_PATH = pathlib.Path(__file__).parent / "views"


class Image:
    def __init__(self, image_path: str, checked=False, master=None) -> None:
        self._image_path = image_path
        self._checked = checked

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_PATH / "image.ui")
        self.mainwindow = builder.get_object('imageFrame', master)
        self.label = builder.get_object('imageLabel')
        self.checkbox = builder.get_object('imageCheckbox')

        image = PILImage.open(image_path)
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
        self.label.configure(image=self._image)
        self.label.image = self._image

        self.checked(checked)

        builder.connect_callbacks(self)

    def checked(self, value):
        self._checked = IntVar(value=0)
        if value:
            self._checked.set(1)
        self.checkbox.configure(variable=self._checked)


class ImageGroup:
    def __init__(self, image_paths: List[str], title="", master=None) -> None:
        self._image_paths = image_paths
        self._images = []

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_PATH / "image_group.ui")
        self.mainwindow = builder.get_object('imageGroup', master)
        self.label = builder.get_object('imageGroupLabel')
        self.image_list = builder.get_object('imageGroupList')

        self.label.configure(text=title)

        for i, path in enumerate(self._image_paths):
            image = Image(path, checked=True, master=self.image_list)
            if i == 0:
                image.checked(False)
            self._images.append(image)
        
        builder.connect_callbacks(self)
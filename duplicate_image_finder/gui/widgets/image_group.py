# Allow Type without quotes
from __future__ import annotations

from tkinter.ttk import Frame, Label
# Allow type checking without importing
from typing import TYPE_CHECKING

from .base import Widget
from .image import Image

if TYPE_CHECKING:
    from finder import ImageInfoGroup

    from ..windows.image import ImageWindow


class ImageGroup(Widget):
    """A group of images"""

    def __init__(self, image_infos: ImageInfoGroup, image_window: ImageWindow, title: str = "", parent=None) -> None:
        super().__init__(parent, "image_group.ui", "imageGroup", Frame)

        self._images: list[Image] = []
        self._image_window = image_window

        self._label: Label = self._builder.get_object('imageGroupLabel')
        self._image_list: Frame = self._builder.get_object('imageGroupList')

        self.title = title
        self.image_infos = image_infos

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self._label.configure(text=self._title)

    @property
    def image_infos(self):
        return self._image_infos

    @image_infos.setter
    def image_infos(self, value):
        self._image_infos = value
        self.load_images()

    @property
    def images(self):
        return self._images

    def load_images(self):
        self._images = []
        for i, image_info in enumerate(self._image_infos):
            image = Image(image_info, parent=self._image_list, image_window=self._image_window)
            self._images.append(image)

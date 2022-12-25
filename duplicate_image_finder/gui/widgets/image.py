# Allow Type without quotes
from __future__ import annotations

from tkinter import IntVar
from tkinter.ttk import Checkbutton, Frame, Label, Style
from typing import Callable

from finder import ImageInfo

from ..graphics import load_image
from .base import Widget


class Image(Widget):
    """An image that can be checked"""

    def __init__(
            self, image_info: ImageInfo, on_enter: Callable[[ImageInfo],
                                                            None],
            on_leave: Callable[[ImageInfo],
                               None],
            parent) -> None:
        super().__init__(parent, "image.ui", "imageFrame", Frame)

        self._on_enter = on_enter
        self._on_leave = on_leave

        self._label: Label = self._builder.get_object('imageLabel')
        self._checkbox: Checkbutton = self._builder.get_object('imageCheckbox')
        Style().map("TCheckbutton", background=[('selected', '#ff6363'), ('', '#63ff63')])

        self.image_info = image_info
        self.checked = image_info.checked

    @property
    def image_info(self):
        return self._image_info

    @image_info.setter
    def image_info(self, value: ImageInfo):
        self._image_info = value
        self._image = load_image(self._image_info.path, width=128)
        self._label.configure(image=self._image)
        self._label.image = self._image  # type: ignore

    @property
    def checked(self):
        return self._checked.get() == 1

    @checked.setter
    def checked(self, value):
        self._checked = IntVar(value=0)
        if value:
            self._checked = IntVar(value=1)
        self._checkbox.configure(variable=self._checked)
        self._checkbox.checked = self._checked  # type: ignore
        self._image_info.checked = self.checked

    def on_enter(self, event=None):
        self._on_enter(self.image_info)

    def on_leave(self, event=None):
        self._on_leave(self.image_info)

    def on_click(self, event=None):
        self.checked = not self.checked

    def on_check(self, event=None):
        self.checked = self.checked

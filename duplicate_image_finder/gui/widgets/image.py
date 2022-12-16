# Allow Type without quotes
from __future__ import annotations

from tkinter import IntVar
from tkinter.ttk import Checkbutton, Frame, Label, Style
# Allow type checking without importing
from typing import TYPE_CHECKING

from finder import ImageInfo

from ..graphics import load_image
from .base import Widget

if TYPE_CHECKING:
    from ..windows.image import ImageWindow


class Image(Widget):
    """An image that can be checked"""

    def __init__(self, image_info: ImageInfo, image_window: ImageWindow, parent) -> None:
        super().__init__(parent, "image.ui", "imageFrame", Frame)

        self._image_window = image_window

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
        self._image_window.title = self._image_info.path
        self._image_window.path = self._image_info.path
        self._image_window.widget.deiconify()

    def on_leave(self, event=None):
        self._image_window.widget.withdraw()

    def on_click(self, event=None):
        self.checked = not self.checked

    def on_check(self, event=None):
        self.checked = self.checked

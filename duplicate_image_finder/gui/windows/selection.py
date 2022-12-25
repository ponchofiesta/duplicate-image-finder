# Allow Type without quotes
from __future__ import annotations

from math import ceil
from tkinter import StringVar
from tkinter.ttk import Entry, Frame, Label, Panedwindow
# Allow type checking without importing
from typing import TYPE_CHECKING

from finder import ImageInfo

from ..graphics import load_image
from ..widgets.image_list import ImageList
from .base import Window

if TYPE_CHECKING:
    from finder import ImageInfoGroup


class SelectionWindow(Window):
    """Image selection window"""

    GROUPS_PER_PAGE = 10

    def __init__(self, groups: list[ImageInfoGroup], parent=None):
        super().__init__(parent, "selection_window.ui", "mainWindow")
        self._cancel = False
        self._groups_frame: Frame = self._builder.get_object("container")
        self._page_entry: Entry = self._builder.get_object("pageEntry")
        self._page_string = StringVar()
        self._page_entry.configure(textvariable=self._page_string)
        self._paned_window: Panedwindow = self._builder.get_object("panedwindow1")
        self._image_preview: Label = self._builder.get_object("image_preview_label")
        self._image_list = ImageList(parent=self._groups_frame,
                                     on_enter=self.on_image_enter, on_leave=self.on_image_leave)
        self._page_total_label: Label = self._builder.get_object("totalPagesLabel")

        # Modal window
        if parent is not None:
            self.widget.grab_set()

        self._page = 0
        self.groups = groups
        self.parent = parent
        self.page = 0

        self.widget.bind("<Return>", self.on_page_change)

    @property
    def page(self) -> int:
        return self._page

    @page.setter
    def page(self, page: int):
        if not self.validate_page(page):
            return
        self._page = page
        self._page_string.set(str(page + 1))
        self.load_images()
        # TODO redraw

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value
        total = str(ceil(len(self._groups) / self.GROUPS_PER_PAGE))
        self._page_total_label.configure(text=total)
        self.load_images()

    def on_ok(self, event=None):
        self.widget.destroy()

    def on_image_enter(self, image_info: ImageInfo):
        width = self._image_preview.winfo_width()
        height = self._image_preview.winfo_height()
        if width <= 0 or height <= 0:
            return
        image = load_image(image_info.path, width=width, height=height)
        self._image_preview.configure(image=image)

    def on_image_leave(self, event=None):
        self._image_preview.configure(image='')

    def on_page_validate(self, page: str):
        return str.isdigit(page) and self.validate_page(int(page) - 1) or page == ''

    def on_page_prev(self, event=None):
        self.page -= 1

    def on_page_next(self, event=None):
        self.page += 1

    def on_page_change(self, event=None):
        page = self._page_entry.get()
        if page == '':
            page = 0
        self.page = int(page) - 1

    def validate_page(self, value: int) -> bool:
        return value >= 0 and value < ceil(len(self.groups) / self.GROUPS_PER_PAGE)

    def load_images(self):
        # Clear old image groups
        self._image_list.clear()

        # Create new image group for page
        start_group = self.page * self.GROUPS_PER_PAGE
        end_group = start_group + self.GROUPS_PER_PAGE
        for i, group in enumerate(self.groups[start_group:end_group]):
            self._image_list.add_group(group, title=f"Group {1 + i + self.page * self.GROUPS_PER_PAGE}")

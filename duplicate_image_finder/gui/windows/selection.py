# Allow Type without quotes
from __future__ import annotations

from math import ceil
from tkinter import StringVar
from tkinter.ttk import Entry, Frame, Label
# Allow type checking without importing
from typing import TYPE_CHECKING

from ..widgets.image_list import ImageList
from .base import Window
from .image import ImageWindow

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
        self._image_window = ImageWindow(parent=self.parent)
        self._image_list = ImageList(parent=self._groups_frame, image_window=self._image_window)
        self._page_total_label: Label = self._builder.get_object("totalPagesLabel")

        # Modal window
        if parent is not None:
            self.widget.transient(parent)
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

    def on_mousemove(self, event=None):
        space = 32
        bottom = 80

        mouse_x = self.widget.winfo_pointerx()
        mouse_y = self.widget.winfo_pointery()
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        window_width = self._image_window.widget.winfo_width()
        window_height = self._image_window.widget.winfo_height()

        if mouse_x > screen_width / 2:
            window_x = mouse_x - window_width - space - space
        else:
            window_x = mouse_x + space

        if mouse_y > screen_height - window_height - bottom:
            window_y = screen_height - window_height + space - bottom
        else:
            window_y = mouse_y + space

        self._image_window.widget.geometry('+%d+%d' % (window_x, window_y))

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

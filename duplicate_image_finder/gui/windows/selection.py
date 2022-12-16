# Allow Type without quotes
from __future__ import annotations

# Allow type checking without importing
from typing import TYPE_CHECKING

from ..widgets.image_group import ImageGroup
from .base import Window
from .image import ImageWindow

if TYPE_CHECKING:
    from finder import ImageInfoGroup


class SelectionWindow(Window):
    """Image selection window"""

    def __init__(self, groups: list[ImageInfoGroup], parent=None):
        super().__init__(parent, "selection_window.ui", "mainWindow")
        self._cancel = False
        self._groups_frame = self._builder.get_object("container")
        self._image_window = ImageWindow(parent=self.parent)
        self.page = 1

        # Modal window
        if parent is not None:
            self.widget.transient(parent)
            self.widget.grab_set()

        self.groups = groups
        self.parent = parent

        self.widget.bind("<Return>", self.on_page_change)

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, page):
        self._page = page
        # TODO redraw

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value
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

    def on_page_validate(self, *event):
        print("validate")
        print(event)

    def on_page_change(self, event=None):
        print("change")
        print(event)

    def load_images(self):
        self._image_groups = []
        for i, group in enumerate(self.groups):
            group = ImageGroup(group, title=f"Group {i}",
                               parent=self._groups_frame.innerframe, image_window=self._image_window)
            self._image_groups.append(group)

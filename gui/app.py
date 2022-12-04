import os
import pathlib
import sys
from tkinter import Toplevel
from typing import List

import pygubu
import tqdm

from gui.components import ImageGroup, ImageWindow, Widget

VIEWS_PATH = pathlib.Path(__file__).parent / "views"


class App(Widget):
    def __init__(self, groups: List, parent=None):
        Widget.__init__(self, parent)
        builder = pygubu.Builder()
        builder.add_resource_path(VIEWS_PATH)
        builder.add_from_file(VIEWS_PATH / "app.ui")
        self.widget: Toplevel = builder.get_object("mainWindow", parent)
        self._groups_frame = builder.get_object("container")

        self._image_window = ImageWindow(parent=self.parent)

        self.groups = groups
        self.parent = parent

        builder.connect_callbacks(self)

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value
        self.load_images()

    @property
    def image_groups(self):
        return self._image_groups

    def on_delete(self, event=None):
        delete_paths = []
        for group in self.image_groups:
            for image in group.images:
                if image.checked:
                    delete_paths.append(image.path)

        print("Removing duplicate images...")
        for path in tqdm.tqdm(delete_paths):
            try:
                os.remove(path)
            except Exception as e:
                print(f"WARNING: Could not remove {path}: {e}", file=sys.stderr)

        self.widget.destroy()

    def on_cancel(self, event=None):
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

    def load_images(self):
        self._image_groups = []
        for i, group in enumerate(self._groups):
            paths = [item["path"] for item in group]
            group = ImageGroup(paths, title=f"Group {i}", parent=self._groups_frame.innerframe, image_window=self._image_window)
            self._image_groups.append(group)

    def run(self):
        self.widget.lift()
        self.widget.attributes('-topmost', True)
        self.widget.after_idle(self.widget.attributes, '-topmost', False)
        self.widget.mainloop()

import os
import pathlib
import sys
import time
from tkinter import Toplevel
from typing import List

import pygubu
import tqdm

from gui.components import ImageGroup

VIEWS_PATH = pathlib.Path(__file__).parent / "views"


class App:
    def __init__(self, groups: List, master=None):
        builder = pygubu.Builder()
        builder.add_resource_path(VIEWS_PATH)
        builder.add_from_file(VIEWS_PATH / "app.ui")
        self.mainwindow: Toplevel = builder.get_object("mainWindow", master)
        self._groups_frame = builder.get_object("container")

        self.groups = groups
        self._master = master

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
                time.sleep(1)
                os.remove(path)
            except Exception as e:
                print(f"WARNING: Could not remove {path}: {e}", file=sys.stderr)

        self.mainwindow.destroy()

    def on_cancel(self, event=None):
        self.mainwindow.destroy()

    def load_images(self):
        self._image_groups = []
        for i, group in enumerate(self._groups):
            paths = [item["path"] for item in group]
            group = ImageGroup(paths, title=f"Group {i}", master=self._groups_frame.innerframe)
            self._image_groups.append(group)

    def run(self):
        self.mainwindow.lift()
        self.mainwindow.attributes('-topmost', True)
        self.mainwindow.after_idle(self.mainwindow.attributes, '-topmost',False)
        self.mainwindow.mainloop()

import pathlib
from tkinter import Canvas, Frame, Scrollbar, Toplevel

import pygubu

from gui.views import ImageGroup

VIEWS_PATH = pathlib.Path(__file__).parent / "views"


class App:
    def __init__(self, groups, master=None):
        builder = pygubu.Builder()
        builder.add_resource_path(VIEWS_PATH)
        builder.add_from_file(VIEWS_PATH / "app.ui")
        self.mainwindow: Toplevel = builder.get_object("mainWindow", master)
        self.groups_frame = builder.get_object("container")
        self._groups = groups
        self._master = master
        builder.connect_callbacks(self)

    def on_delete(self, event=None):
        pass

    def on_cancel(self, event=None):
        self.mainwindow.destroy()

    def run(self):
        for i, group in enumerate(self._groups):
            paths = [item["path"] for item in group]
            group = ImageGroup(paths, title=f"Group {i}", master=self.groups_frame)

        self.mainwindow.mainloop()

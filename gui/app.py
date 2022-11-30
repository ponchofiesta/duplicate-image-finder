import pathlib
#import tkinter as tk
import pygubu
#from gui.models import GroupsModel
#from gui.views import GroupsView
#from gui.controller import GroupsController
from gui.views import Image, ImageGroup

PROJECT_PATH = pathlib.Path(__file__).parent / "views"
PROJECT_UI = PROJECT_PATH / "app.ui"

class App:
    def __init__(self, groups, master=None):
        builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object("mainWindow", master)
        self.groups_frame = builder.get_object("groupsFrame")
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
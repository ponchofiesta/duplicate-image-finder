import os
import pathlib
from tkinter import filedialog
from typing import List

from finder import DuplicateFinder
from gui.components import ProgressWindow, SelectionWindow

VIEWS_PATH = pathlib.Path(__file__).parent / "views"


class App:
    def run(self):
        directory = filedialog.askdirectory(initialdir=os.getcwd())
        if directory == '':
            exit()
        print(directory)

        finder = DuplicateFinder()

        app = App()

        progress_window = ProgressWindow(cancel_handler=self.on_cancel)

        pairs = finder.find(directory, progress_handler=self.on_progress)
        groups = finder.get_groups(pairs)

        selection_window = SelectionWindow(groups)
        selection_window.run()
        
    def on_progress(self, value, status):
        pass

    def on_cancel(self):
        pass


if __name__ == "__main__":
    app = App()
    app.run()
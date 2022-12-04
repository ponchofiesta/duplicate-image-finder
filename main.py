import os
from tkinter import filedialog

from finder import DuplicateFinder
from gui.app import App

if __name__ == "__main__":
    directory = filedialog.askdirectory(initialdir=os.getcwd())
    if directory == '':
        exit()
    print(directory)

    finder = DuplicateFinder()
    pairs = finder.find(directory, progress=True)
    groups = finder.get_groups(pairs)

    app = App(groups)
    app.run()

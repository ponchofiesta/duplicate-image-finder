import os
from tkinter import filedialog
from gui.app import App
from finder import DuplicateFinder


if __name__ == "__main__":
    directory = filedialog.askdirectory(initialdir=os.getcwd())
    print(directory)


    finder = DuplicateFinder()
    pairs = finder.find(directory, progress=True)
    groups = finder.get_groups(pairs)

    app = App(groups)
    app.run()
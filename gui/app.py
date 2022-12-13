import os
import pathlib
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from tkinter import filedialog

from finder import DuplicateFinder, ImageInfoGroup, ImageInfo
from gui.components import MainWindow, ProgressMessage, ProgressWindow, SelectionWindow

VIEWS_PATH = pathlib.Path(__file__).parent / "views"


class App:
    def __init__(self) -> None:
        self._progress_running = False

    def run(self):
        main_window = MainWindow()
        main_window.run()

        # directory = os.getcwd()
        # while True:
        #     directory = filedialog.askdirectory(initialdir=directory)
        #     #directory = OpenWindow().get_directory()
        #     if directory == '':
        #         return

        #     self._queue: Queue[ProgressMessage] = Queue()
        #     finder = DuplicateFinder()

        #     def on_cancel():
        #         finder.cancel = True

        #     self._progress_window = ProgressWindow(self._queue, cancel_handler=on_cancel)

        #     def find_runner():
        #         groups = finder.find(directory, progress_handler=self.on_progress)
        #         self._progress_running = False
        #         return groups

        #     self._progress_running = True
        #     with ThreadPoolExecutor(max_workers=1) as executor:
        #         future = executor.submit(find_runner)
        #         self.progress_loop()
        #         self._progress_window.run()
        #         groups: list[ImageInfoGroup] = future.result()

        #     if finder.cancel:
        #         continue

        #     selection_window = SelectionWindow(groups)
        #     selection_window.run()

    # def on_progress(self, value, status):
    #     self._queue.put(ProgressMessage(status=status, value=value))

    # def progress_loop(self):
    #     self._progress_window.process()
    #     if self._progress_running:
    #         self._progress_window.widget.after(200, self.progress_loop)
    #     else:
    #         self._progress_window.widget.destroy()

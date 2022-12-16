import os
import sys
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path
from queue import Queue
from tkinter import filedialog, messagebox
from tkinter.ttk import Frame, Label

from finder import DuplicateFinder, ImageInfoGroup

from .base import Window
from .progress import ProgressMessage, ProgressWindow
from .selection import SelectionWindow


class Step(Enum):
    Open = 0
    Select = 1
    Delete = 2


class MainWindow(Window):
    """Main program window"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent, "main_window.ui", "main_window")
        self._frame_open: Frame = self._builder.get_object("frameOpen")
        self._frame_select: Frame = self._builder.get_object("frameSelect")
        self._frame_delete: Frame = self._builder.get_object("frameDelete")
        self._label_open_status: Label = self._builder.get_object("labelOpenStatus")
        self._label_path: Label = self._builder.get_object("labelPath")
        self._label_select_status: Label = self._builder.get_object("labelSelectStatus")
        self._label_delete_status: Label = self._builder.get_object("labelDeleteStatus")

        self.step = Step.Open
        self.directory = ''
        self._queue: Queue[ProgressMessage]
        self._groups = []
        self._failed = []
        self.groups = []
        self.failed = []

    @property
    def step(self) -> Step:
        return self._step

    @step.setter
    def step(self, value: Step):
        self._step = value
        if value == Step.Open:
            self._change_state(self._frame_select, (tk.DISABLED,))
            self._change_state(self._frame_delete, (tk.DISABLED,))
        elif value == Step.Select:
            self._change_state(self._frame_select, (f'!{tk.DISABLED}',))
            self._change_state(self._frame_delete, (tk.DISABLED,))
        elif value == Step.Delete:
            self._change_state(self._frame_select, (f'!{tk.DISABLED}',))
            self._change_state(self._frame_delete, (f'!{tk.DISABLED}',))

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value: list[ImageInfoGroup]):
        self._groups = value
        self._set_open_status()

    @property
    def failed(self) -> list[Path]:
        return self._failed

    @failed.setter
    def failed(self, failed: list[Path]):
        self._failed = failed
        self._set_open_status()

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, value):
        self._directory = value
        self._label_path.configure(text=value)

    def _set_open_status(self):
        groups_count = len(self.groups)
        images_count = sum([len(group) for group in self.groups])
        dups_count = images_count - groups_count
        failed_count = len(self.failed)
        status = f"{dups_count} duplicates in {groups_count} groups found."
        if failed_count > 0:
            status = f"{status} {failed_count} images could not be analyzed."
        self._label_open_status.configure(text=status)

    def _change_state(self, widget, state: tuple[str, ...]):
        for child in widget.winfo_children():
            child.state(state)
        widget.state(state)

    def on_open(self, event=None):
        self.directory = filedialog.askdirectory(initialdir=self.directory)
        if self.directory == '':
            return

        self._queue = Queue()
        finder = DuplicateFinder()

        def on_cancel():
            finder.cancel = True

        self._progress_window = ProgressWindow(self._queue, cancel_handler=on_cancel, parent=self.widget)

        def on_progress(value, status):
            self._queue.put(ProgressMessage(status=status, value=value))

        def progress_loop():
            self._progress_window.process()
            if self._progress_running:
                self._progress_window.widget.after(200, progress_loop)
            else:
                self._progress_window.widget.destroy()

        def find_runner():
            (groups, failed) = finder.find(self.directory, progress_handler=on_progress)
            self._progress_running = False
            return (groups, failed)

        self._progress_running = True
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(find_runner)
            progress_loop()
            self.widget.wait_window(self._progress_window.widget)
            (self.groups, self.failed) = future.result()

        if finder.cancel:
            return

        self.step = Step.Select

    def on_select(self, event=None):
        selection_window = SelectionWindow(self.groups, parent=self.widget)
        self.widget.wait_window(selection_window.widget)
        self.groups = selection_window.groups

        dups_count = 0
        for group in self.groups:
            for image in group:
                if image.checked:
                    dups_count += 1

        self._label_select_status.configure(text=f"{dups_count} images to be removed")

        if dups_count > 0:
            self.step = Step.Delete

    def on_delete(self, event=None):
        if not messagebox.askokcancel("Delete duplicates", "Are you sure to delete selected images?"):
            return

        delete_paths = []
        for group in self.groups:
            for image in group:
                if image.checked:
                    delete_paths.append(image.path)

        self._queue: Queue[ProgressMessage] = Queue()
        self._cancel = False

        def on_cancel():
            self._cancel = True

        self._progress_window = ProgressWindow(self._queue, cancel_handler=on_cancel, parent=self.widget)

        def on_progress(value, status):
            self._queue.put(ProgressMessage(value=value, status=status))

        def progress_loop():
            self._progress_window.process()
            if self._progress_running:
                self._progress_window.widget.after(200, progress_loop)
            else:
                self._progress_window.widget.destroy()
                messagebox.showinfo("Success", "Duplicate images were removed.")

        def remove_runner():
            total = len(delete_paths)
            succeeded = []
            failed = []
            for i, path in enumerate(delete_paths):
                try:
                    if self._cancel:
                        return (succeeded, failed)
                    os.remove(path)
                    succeeded.append(path)
                except Exception as e:
                    print(f"WARNING: Could not remove {path}: {e}", file=sys.stderr)
                    failed.append(path)
                on_progress(i / total * 100, "Removing duplicate images...")
            self._progress_running = False
            return (succeeded, failed)

        self._progress_running = True
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(remove_runner)
            progress_loop()
            self.widget.wait_window(self._progress_window.widget)
            (succeeded, failed) = future.result()

        status = f"{len(succeeded)} successfully removed."
        if len(failed) > 0:
            status = f"{status} {len(failed)} failed to remove."
        self._label_delete_status.configure(text=status)

import queue
from dataclasses import dataclass
from queue import Queue
from tkinter.ttk import Button, Label, Progressbar
from typing import Callable

from .base import Window


@dataclass
class ProgressMessage:
    status: str
    value: int


class ProgressWindow(Window):
    """Window to shop a process progress"""

    def __init__(self, queue: Queue[ProgressMessage], cancel_handler: Callable, parent=None) -> None:
        super().__init__(parent, "progress_window.ui", "windowMain")

        self._queue = queue
        self._cancel_handler = cancel_handler

        if parent is not None:
            # Modal window
            self.widget.transient(parent)
            self.widget.grab_set()

            # Center window to parent window
            self.widget.update_idletasks()
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            width = self.widget.winfo_width()
            height = self.widget.winfo_height()
            x = parent_x + (parent_width // 2 - width // 2)
            y = parent_y + (parent_height // 2 - height // 2)
            self.widget.geometry(f'+{x}+{y}')

        self._label_status: Label = self._builder.get_object('labelStatus')
        self._progressbar: Progressbar = self._builder.get_object('progressbar')
        self._button_cancel: Button = self._builder.get_object('buttonCancel')

    def process(self):
        if self._queue.qsize() == 0:
            return
        msg = None
        while True:
            try:
                msg = self._queue.get(False)
            except queue.Empty:
                break
        if msg is None:
            return
        if msg.status is not None:
            self._label_status.configure(text=msg.status)
        self._progressbar.configure(value=msg.value)

    def on_cancel(self, event=None):
        if self._cancel_handler is not None:
            self._cancel_handler()

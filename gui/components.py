import os
import pathlib
import queue
import sys
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from queue import Queue
from tkinter import IntVar, Toplevel, filedialog, messagebox
from tkinter.ttk import Button, Checkbutton, Frame, Label, Progressbar, Style
from typing import Callable, Generic, TypeVar

import pygubu

from finder import DuplicateFinder, ImageInfo, ImageInfoGroup
from gui.graphics import load_image

VIEWS_PATH = pathlib.Path(__file__).parent / "views"

T = TypeVar('T')


class Widget(Generic[T]):
    """Base GUI class for app Tk widgets"""

    def __init__(self, parent, file: str, id: str, widget_type: T) -> None:
        self._parent = parent
        self._builder = pygubu.Builder()
        self._builder.add_resource_path(VIEWS_PATH)
        self._builder.add_from_file(VIEWS_PATH / file)
        self._widget: T = self._builder.get_object(id, self.parent)
        self._builder.connect_callbacks(self)

    @property
    def widget(self):
        """Tk widget behind this class"""
        return self._widget

    @widget.setter
    def widget(self, value):
        self._widget = value

    @property
    def parent(self):
        """Parent Tk widget of this widget"""
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value


class Window(Widget):
    """Base Window class for app"""

    def __init__(self, parent, file: str, id: str) -> None:
        super().__init__(parent, file, id, Toplevel)

    def run(self):
        self.widget.lift()
        self.widget.attributes('-topmost', True)  # type: ignore
        self.widget.after_idle(self.widget.attributes, '-topmost', False)  # type: ignore
        self.widget.mainloop()


class Image(Widget):
    """An image that can be checked"""
    def __init__(self, image_info: ImageInfo, image_window: 'ImageWindow', parent) -> None:
        super().__init__(parent, "image.ui", "imageFrame", Frame)

        self._image_window = image_window

        self._label: Label = self._builder.get_object('imageLabel')
        self._checkbox: Checkbutton = self._builder.get_object('imageCheckbox')
        Style().map("TCheckbutton", background=[('selected', '#ff6363'), ('', '#63ff63')])

        self.image_info = image_info
        self.checked = image_info.checked

    @property
    def image_info(self):
        return self._image_info

    @image_info.setter
    def image_info(self, value: ImageInfo):
        self._image_info = value
        self._image = load_image(self._image_info.path, width=128)
        self._label.configure(image=self._image)
        self._label.image = self._image  # type: ignore

    @property
    def checked(self):
        return self._checked.get() == 1

    @checked.setter
    def checked(self, value):
        self._checked = IntVar(value=0)
        if value:
            self._checked = IntVar(value=1)
        self._checkbox.configure(variable=self._checked)
        self._checkbox.checked = self._checked  # type: ignore
        self._image_info.checked = self.checked

    def on_enter(self, event=None):
        self._image_window.title = self._image_info.path
        self._image_window.path = self._image_info.path
        self._image_window.widget.deiconify()

    def on_leave(self, event=None):
        self._image_window.widget.withdraw()

    def on_click(self, event=None):
        self.checked = not self.checked

    def on_check(self, event=None):
        self.checked = self.checked


class ImageGroup(Widget):
    """A group of images"""
    def __init__(self, image_infos: ImageInfoGroup, image_window: 'ImageWindow', title: str = "", parent=None) -> None:
        super().__init__(parent, "image_group.ui", "imageGroup", Frame)

        self._images: list[Image] = []
        self._image_window = image_window

        self._label: Label = self._builder.get_object('imageGroupLabel')
        self._image_list: Frame = self._builder.get_object('imageGroupList')

        self.title = title
        self.image_infos = image_infos

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self._label.configure(text=self._title)

    @property
    def image_infos(self):
        return self._image_infos

    @image_infos.setter
    def image_infos(self, value):
        self._image_infos = value
        self.load_images()

    @property
    def images(self):
        return self._images

    def load_images(self):
        self._images = []
        for i, image_info in enumerate(self._image_infos):
            image = Image(image_info, parent=self._image_list, image_window=self._image_window)
            self._images.append(image)


class ImageWindow(Window):
    """An image preview popup window"""
    def __init__(self, title="", path=None, parent=None) -> None:
        super().__init__(parent, "image_window.ui", "imageWindow")

        self._label_title = self._builder.get_object('labelTitle')
        self._label_image = self._builder.get_object('labelImage')

        self.widget.withdraw()
        self.widget.overrideredirect(True)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self._label_title.configure(text=self._title)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        screen_height = self.widget.winfo_screenheight()
        image = load_image(self._path, width=screen_height * 0.8)
        self._label_image.image = image
        self._label_image.configure(image=image)

    def on_configure_title(self, event=None):
        self._label_title.configure(wraplength=self._label_image.winfo_width())


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

        # Modal window
        if parent is not None:
            self.widget.transient(parent)
            self.widget.grab_set()

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


class SelectionWindow(Window):
    """Image selection window"""
    def __init__(self, groups: list[ImageInfoGroup], parent=None):
        super().__init__(parent, "selection_window.ui", "mainWindow")
        self._cancel = False

        self._groups_frame = self._builder.get_object("container")

        self._image_window = ImageWindow(parent=self.parent)

        self.groups = groups
        self.parent = parent

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value
        self.load_images()

    def on_ok(self, event=None):
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
        for i, group in enumerate(self.groups):
            group = ImageGroup(group, title=f"Group {i}",
                               parent=self._groups_frame.innerframe, image_window=self._image_window)
            self._image_groups.append(group)


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

        self.step = 0
        self.directory = ''
        self._queue: Queue[ProgressMessage]
        self.groups = []

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, value: int):
        self._step = value
        if value == 0:
            self._change_state(self._frame_select, (tk.DISABLED,))
            self._change_state(self._frame_delete, (tk.DISABLED,))
        elif value == 1:
            self._change_state(self._frame_select, (f'!{tk.DISABLED}',))
            self._change_state(self._frame_delete, (tk.DISABLED,))
        elif value == 2:
            self._change_state(self._frame_select, (f'!{tk.DISABLED}',))
            self._change_state(self._frame_delete, (f'!{tk.DISABLED}',))

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value: list[ImageInfoGroup]):
        self._groups = value
        groups_count = len(value)
        images_count = sum([len(group) for group in value])
        dups_count = images_count - groups_count
        self._label_open_status.configure(text=f"{dups_count} duplicates in {groups_count} groups found")

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, value):
        self._directory = value
        self._label_path.configure(text=value)

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
            groups = finder.find(self.directory, progress_handler=on_progress)
            self._progress_running = False
            return groups

        self._progress_running = True
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(find_runner)
            progress_loop()
            self.widget.wait_window(self._progress_window.widget)
            self.groups = future.result()

        if finder.cancel:
            return

        self.step = 1

    def on_select(self, event=None):
        selection_window = SelectionWindow(self.groups)
        self.widget.wait_window(selection_window.widget)
        self.groups = selection_window.groups

        dups_count = 0
        for group in self.groups:
            for image in group:
                if image.checked:
                    dups_count += 1

        self._label_select_status.configure(text=f"{dups_count} images to be removed")

        if dups_count > 0:
            self.step = 2

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
            for i, path in enumerate(delete_paths):
                try:
                    if self._cancel:
                        return
                    os.remove(path)
                except Exception as e:
                    print(f"WARNING: Could not remove {path}: {e}", file=sys.stderr)
                on_progress(i / total * 100, "Removing duplicate images...")
            self._progress_running = False

        self._progress_running = True
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(remove_runner)
            progress_loop()
            self.widget.wait_window(self._progress_window.widget)

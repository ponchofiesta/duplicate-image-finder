from dataclasses import dataclass
import os
import pathlib
import queue
import sys
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from tkinter import IntVar, Toplevel, messagebox
from tkinter.ttk import Button, Checkbutton, Frame, Label, Progressbar, Style
from typing import Callable, Generic, TypeVar

import pygubu

from finder import ImageInfoGroup, ImageInfo
from gui.graphics import load_image

#from tkinterdnd2 import DND_FILES


VIEWS_PATH = pathlib.Path(__file__).parent / "views"

T = TypeVar('T')

class Widget(Generic[T]):
    def __init__(self, parent, file: str, id: str, widget_type: T) -> None:
        self._parent = parent
        self._builder = pygubu.Builder()
        self._builder.add_resource_path(VIEWS_PATH)
        self._builder.add_from_file(VIEWS_PATH / file)
        self._widget: T = self._builder.get_object(id, self.parent)
        self._builder.connect_callbacks(self)

    @property
    def widget(self):
        return self._widget

    @widget.setter
    def widget(self, value):
        self._widget = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value


class Window(Widget):
    def __init__(self, parent, file: str, id: str) -> None:
        super().__init__(parent, file, id, Toplevel)

    def run(self):
        self.widget.lift()
        self.widget.attributes('-topmost', True)  # type: ignore
        self.widget.after_idle(self.widget.attributes, '-topmost', False)  # type: ignore
        self.widget.mainloop()
    

class Image(Widget):
    def __init__(self, path: str, image_window: 'ImageWindow', parent, checked: bool = False, ) -> None:
        super().__init__(parent, "image.ui", "imageFrame", Frame)

        self._image_window = image_window

        self._label: Label = self._builder.get_object('imageLabel')
        self._checkbox: Checkbutton = self._builder.get_object('imageCheckbox')
        Style().map("TCheckbutton", background=[('selected', '#ff6363'), ('', '#63ff63')])

        self.path = path
        self.checked = checked

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        self._image = load_image(self._path, width=128)
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

    def on_enter(self, event=None):
        self._image_window.title = self.path
        self._image_window.path = self.path
        self._image_window.widget.deiconify()

    def on_leave(self, event=None):
        self._image_window.widget.withdraw()

    def on_click(self, event=None):
        self.checked = not self.checked


class ImageGroup(Widget):
    def __init__(self, image_paths: list[str], image_window: 'ImageWindow', title: str = "", parent=None) -> None:
        super().__init__(parent, "image_group.ui", "imageGroup", Frame)

        self._images: list[Image] = []
        self._image_window = image_window

        self._label: Label = self._builder.get_object('imageGroupLabel')
        self._image_list: Frame = self._builder.get_object('imageGroupList')

        self.title = title
        self.paths = image_paths

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self._label.configure(text=self._title)

    @property
    def paths(self):
        return self._image_paths

    @paths.setter
    def paths(self, value):
        self._image_paths = value
        self.load_images()

    @property
    def images(self):
        return self._images

    def load_images(self):
        self._images = []
        for i, path in enumerate(self._image_paths):
            image = Image(path, checked=True, parent=self._image_list, image_window=self._image_window)
            if i == 0:
                image.checked = False
            self._images.append(image)


class ImageWindow(Window):
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
    def __init__(self, groups: list[ImageInfoGroup], parent=None):
        super().__init__(parent, "app.ui", "mainWindow")
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

    @property
    def image_groups(self):
        return self._image_groups

    def on_delete(self, event=None):
        delete_paths = []
        for group in self.image_groups:
            for image in group.images:
                if image.checked:
                    delete_paths.append(image.path)

        self._queue: Queue[ProgressMessage] = Queue()
        self._cancel = False

        def on_cancel():
            self._cancel = True

        self._progress_window = ProgressWindow(self._queue, cancel_handler=on_cancel, parent=self.widget)

        def remove_runner():
            total = len(delete_paths)
            for i, path in enumerate(delete_paths):
                try:
                    if self._cancel:
                        return
                    os.remove(path)
                    self.on_progress(i / total * 100, "Removing duplicate images...")
                except Exception as e:
                    print(f"WARNING: Could not remove {path}: {e}", file=sys.stderr)
            self._progress_running = False

        self._progress_running = True
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(remove_runner)
            self.progress_loop()
            self.widget.wait_window(self._progress_window.widget)

    def on_cancel(self, event=None):
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
        for i, group in enumerate(self._groups):
            paths = [item.path for item in group]
            group = ImageGroup(paths, title=f"Group {i}",
                               parent=self._groups_frame.innerframe, image_window=self._image_window)
            self._image_groups.append(group)

    def on_progress(self, value, status):
        self._queue.put(ProgressMessage(value=value, status=status))

    def progress_loop(self):
        self._progress_window.process()
        if self._progress_running:
            self._progress_window.widget.after(200, self.progress_loop)
        else:
            self._progress_window.widget.destroy()
            self.widget.destroy()
            messagebox.showinfo("Success", "Duplicate images were removed.")


# class OpenWindow(Widget):
#     def __init__(self, parent: BaseWidget = None) -> None:
#         super().__init__(parent)
#         self.load_view("open_window.ui", "openWindow")
#         self.widget.drop_target_register(DND_FILES)
#         self.widget.dnd_bind("<<Drop>>", self.on_drop)

#     def get_directory(self, initialdir=os.getcwd()):
#         self._directory = initialdir
#         self.run()
#         return self._directory

#     def on_click(self):
#         self._directory = filedialog.askdirectory(initialdir=self._directory)
#         self.widget.destroy()

#     def on_drop(self, event):
#         print(event)

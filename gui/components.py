import pathlib
from tkinter import BaseWidget, Frame, IntVar, Label, Toplevel, Checkbutton
import tkinter
from tkinter.ttk import Style
from typing import List

import pygubu

from gui.graphics import load_image

VIEWS_PATH = pathlib.Path(__file__).parent / "views"


class Widget:
    def __init__(self, parent: BaseWidget) -> None:
        self._widget = None
        self._parent = parent

    @property
    def widget(self) -> BaseWidget:
        return self._widget

    @widget.setter
    def widget(self, value: BaseWidget):
        self._widget = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value: BaseWidget):
        self._parent = value
    

class Image(Widget):
    def __init__(self, path: str, checked=False, parent=None, image_window=None) -> None:
        Widget.__init__(self, parent)
        
        self._image_window = image_window

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(VIEWS_PATH)
        builder.add_from_file(VIEWS_PATH / "image.ui")
        self.widget: Frame = builder.get_object('imageFrame', parent)
        self._label: Label = builder.get_object('imageLabel')
        self._checkbox: Checkbutton = builder.get_object('imageCheckbox')
        Style().map("TCheckbutton", background=[('selected', '#ff6363'), ('', '#63ff63')])

        self.path = path
        self.checked = checked

        builder.connect_callbacks(self)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == getattr(self, "_path", None):
            return

        self._path = value

        self._image = load_image(self._path, width=128)

        self._label.configure(image=self._image)
        self._label.image = self._image

    @property
    def checked(self):
        return self._checked.get() == 1

    @checked.setter
    def checked(self, value):
        self._checked = IntVar(value=0)
        if value:
            self._checked = IntVar(value=1)
        # style = Style(self._checkbox)
        # style.configure('TCheckbutton', background='#ff6363')
        self._checkbox.configure(variable=self._checked)
        self._checkbox.checked = self._checked

    def on_enter(self, event=None):
        self._image_window.title = self.path
        self._image_window.path = self.path
        self._image_window.widget.deiconify()
    
    def on_leave(self, event=None):
        self._image_window.widget.withdraw()
    
    def on_click(self, event=None):
        self.checked = not self.checked


class ImageGroup(Widget):
    def __init__(self, image_paths: List[str], title="", image_window=None, parent=None) -> None:
        Widget.__init__(self, parent)

        self._images: List[Image] = []
        self._image_window = image_window

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(VIEWS_PATH)
        builder.add_from_file(VIEWS_PATH / "image_group.ui")
        self._widget: Frame = builder.get_object('imageGroup', parent)
        self._label: Label = builder.get_object('imageGroupLabel')
        self._image_list: Frame = builder.get_object('imageGroupList')

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


class ImageWindow(Widget):
    def __init__(self, title="", path=None, parent=None) -> None:
        Widget.__init__(self, parent)
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(VIEWS_PATH)
        builder.add_from_file(VIEWS_PATH / "image_window.ui")
        self.widget: Toplevel = builder.get_object('imageWindow', parent)
        self._label_title = builder.get_object('labelTitle')
        self._label_image = builder.get_object('labelImage')

        self.widget.withdraw()
        self.widget.overrideredirect(True)

        builder.connect_callbacks(self)
    

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

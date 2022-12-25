from tkinter import END, Text
from tkinter.ttk import Label, Scrollbar, Style
from typing import Callable

from finder import ImageInfo, ImageInfoGroup

from .base import Widget
from .image import Image


class ImageList(Widget):
    def __init__(self, parent, on_enter: Callable[[ImageInfo], None], on_leave: Callable[[ImageInfo], None]) -> None:
        super().__init__(parent, None, None, Text)
        self._on_enter = on_enter
        self._on_leave = on_leave
        background = Style().lookup('TFrame', 'background')
        self._widget: Text = Text(master=parent, background=background, cursor='arrow', wrap='char', borderwidth=0)
        self._widget.pack(expand=True, fill='both', side='left')
        self._scrollbar = Scrollbar(master=parent, command=self._widget.yview)
        self._widget.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.pack(side='right', fill='y')

    def add_group(self, group: ImageInfoGroup, title: str):
        self.widget.configure(state='normal')

        # Add group label
        label = Label(master=self.widget, text=title)

        self.widget.window_create(END, window=label)
        self.widget.insert(END, '\n')

        # Add images of group
        for image_info in group:
            image = Image(image_info, parent=self.widget, on_enter=self._on_enter, on_leave=self._on_leave)
            self.widget.window_create(END, window=image.widget)
        self.widget.insert(END, '\n')

        self.widget.configure(state='disabled')

    def clear(self):
        self.widget.configure(state='normal')
        self.widget.delete('1.0', END)
        children = self.widget.winfo_children()
        for child in children:
            print("clear")
            child.pack_forget()
        self.widget.configure(state='disabled')

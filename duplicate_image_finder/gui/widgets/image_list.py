from tkinter import END, Text
from tkinter.ttk import Label, Scrollbar, Style

from finder import ImageInfoGroup

from ..windows.image import ImageWindow
from .base import Widget
from .image import Image


class ImageList(Widget):
    def __init__(self, parent, image_window: ImageWindow) -> None:
        super().__init__(parent, None, None, Text)
        self._image_window = image_window
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
            image = Image(image_info, parent=self.widget, image_window=self._image_window)
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

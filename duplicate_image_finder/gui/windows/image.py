from .base import Window
from ..graphics import load_image

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

from tkinter import Toplevel
from ..widgets.base import Widget

class Window(Widget):
    """Base Window class for app"""

    def __init__(self, parent, file: str, id: str) -> None:
        super().__init__(parent, file, id, Toplevel)

    def run(self):
        self.widget.lift()
        self.widget.attributes('-topmost', True)  # type: ignore
        self.widget.after_idle(self.widget.attributes, '-topmost', False)  # type: ignore
        self.widget.mainloop()
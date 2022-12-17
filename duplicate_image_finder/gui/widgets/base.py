from typing import Generic, Optional, TypeVar

import pygubu

from .. import VIEWS_PATH

T = TypeVar('T')


class Widget(Generic[T]):
    """Base GUI class for app Tk widgets"""

    def __init__(self, parent, file: Optional[str], id: Optional[str], widget_type: T) -> None:
        self._parent = parent
        self._widget: T
        if file is not None and id is not None:
            self._builder = pygubu.Builder()
            self._builder.add_resource_path(VIEWS_PATH)
            self._builder.add_from_file(VIEWS_PATH / file)
            self._widget = self._builder.get_object(id, self.parent)
            self._builder.connect_callbacks(self)

    @property
    def widget(self) -> T:
        """Tk widget behind this class"""
        return self._widget

    @widget.setter
    def widget(self, value: T):
        self._widget = value

    @property
    def parent(self):
        """Parent Tk widget of this widget"""
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

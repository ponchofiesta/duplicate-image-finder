from typing import Generic, TypeVar

import pygubu

from .. import VIEWS_PATH

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

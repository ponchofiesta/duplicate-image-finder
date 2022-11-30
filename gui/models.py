class GroupsModel:
    def __init__(self, groups):
        self._groups = groups

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value

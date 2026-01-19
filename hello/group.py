from dataclasses import dataclass
from enum import Enum


class GroupPrefix(Enum):
    HELLO = 'hello'
    QUERY = 'query'


class IGroup:

    def hello(self) -> str:
        raise NotImplementedError()

    def query(self) -> str:
        raise NotImplementedError()


class Group(IGroup):
    def __init__(self, name: str) -> None:
        self.name = name

    def hello(self) -> str:
        return self._prefix(GroupPrefix.HELLO)

    def query(self) -> str:
        return self._prefix(GroupPrefix.QUERY)

    def _prefix(self, group_type: GroupPrefix) -> str:
        return f'{group_type.value}:{self.name}'

    def __repr__(self) -> str:
        return self.name


@dataclass
class GroupAccess:
    access_url: str
    full_group: str

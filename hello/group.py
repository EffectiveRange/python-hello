from dataclasses import dataclass
from enum import Enum


class GroupPrefix(Enum):
    HELLO = 'hello'
    QUERY = 'query'


@dataclass
class Group:
    name: str
    url: str

    def hello(self) -> 'PrefixedGroup':
        return PrefixedGroup(self, GroupPrefix.HELLO)

    def query(self) -> 'PrefixedGroup':
        return PrefixedGroup(self, GroupPrefix.QUERY)


@dataclass
class PrefixedGroup:
    group: Group
    prefix: GroupPrefix

    @property
    def name(self) -> str:
        return f'{self.prefix.value}:{self.group.name}'

    @property
    def url(self) -> str:
        return self.group.url

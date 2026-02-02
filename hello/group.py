# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

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
        return PrefixedGroup(GroupPrefix.HELLO, self)

    def query(self) -> 'PrefixedGroup':
        return PrefixedGroup(GroupPrefix.QUERY, self)


@dataclass
class PrefixedGroup:
    prefix: GroupPrefix
    group: Group

    @property
    def name(self) -> str:
        return f'{self.prefix.value}:{self.group.name}'

    @property
    def url(self) -> str:
        return self.group.url

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from enum import Enum

import netifaces


@dataclass
class GroupUrl:
    address: str
    port: int
    protocol: str = 'udp'
    interface: str | None = None

    def resolve(self) -> str:
        if self.interface and self.interface in netifaces.interfaces():
            inet_address = netifaces.ifaddresses(self.interface).get(netifaces.AF_INET)
            if inet_address and len(inet_address) > 0:
                address = inet_address[0].get('addr')
                return f'{self.protocol}://{address};{self.address}:{self.port}'

        return f'{self.protocol}://{self.address}:{self.port}'


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

    @staticmethod
    def create(name: str, url: GroupUrl) -> 'Group':
        return Group(name, url.resolve())


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

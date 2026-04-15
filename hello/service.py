# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class Service:
    uuid: UUID
    name: str
    role: str
    urls: dict[str, str] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)
    address: str | None = None

    def __repr__(self) -> str:
        return (f"Service(uuid='{self.uuid}', name='{self.name}', role='{self.role}', "
                f"urls={self.urls}, info={self.info}, address='{self.address}')")

    def to_dict(self) -> dict[str, Any]:
        return {
            'uuid': str(self.uuid),
            'name': self.name,
            'role': self.role,
            'urls': self.urls,
            'info': self.info,
            'address': self.address,
        }


@dataclass
class ServiceQuery(object):
    name: str
    role: str


class ServiceMatcher(object):

    def __init__(self, query: ServiceQuery) -> None:
        self.query = query
        self._name_matcher = re.compile(self.query.name)
        self._role_matcher = re.compile(self.query.role)

    def matches(self, service: Service) -> bool:
        name_match = self._name_matcher.match(service.name)
        role_match = self._role_matcher.match(service.role)
        return bool(name_match and role_match)

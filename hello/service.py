# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class ServiceInfo:
    uuid: UUID
    name: str
    role: str
    urls: dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"ServiceInfo(uuid='{self.uuid}', name='{self.name}', role='{self.role}', urls='{self.urls}')"

    def to_dict(self) -> dict[str, Any]:
        return {
            'uuid': str(self.uuid),
            'name': self.name,
            'role': self.role,
            'urls': self.urls
        }


@dataclass
class ServiceQuery(object):
    name_filter: str
    role_filter: str


class ServiceMatcher(object):

    def __init__(self, query: ServiceQuery) -> None:
        self.query = query
        self._name_matcher = re.compile(self.query.name_filter)
        self._role_matcher = re.compile(self.query.role_filter)

    def matches(self, info: ServiceInfo) -> bool:
        name_match = self._name_matcher.match(info.name)
        role_match = self._role_matcher.match(info.role)
        return bool(name_match and role_match)

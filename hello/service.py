import re
from dataclasses import dataclass


@dataclass
class ServiceInfo:
    name: str
    role: str
    url: str


@dataclass
class ServiceQuery(object):
    name: str
    role: str


class ServiceMatcher(object):

    def __init__(self, query: ServiceQuery) -> None:
        self.query = query
        self._name_matcher = re.compile(self.query.name)
        self._role_matcher = re.compile(self.query.role)

    def matches(self, info: ServiceInfo) -> bool:
        name_match = self._name_matcher.match(info.name)
        role_match = self._role_matcher.match(info.role)
        return bool(name_match and role_match)

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from context_logger import get_logger

from hello import Group, ServiceQuery, Sender, Receiver, GroupAccess, ServiceInfo, ServiceMatcher

log = get_logger('Discoverer')


class DiscoveryEventType(Enum):
    DISCOVERED = 'discovered'
    UPDATED = 'updated'


@dataclass
class DiscoveryEvent:
    service: ServiceInfo
    type: DiscoveryEventType


class OnDiscoveryEvent(Protocol):
    def __call__(self, event: DiscoveryEvent) -> None: ...


class Discoverer:

    def start(self, address: str, group: Group, query: ServiceQuery | None = None) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def discover(self, query: ServiceQuery | None = None) -> None:
        raise NotImplementedError()

    def get_services(self) -> dict[str, ServiceInfo]:
        raise NotImplementedError()

    def register(self, handler: OnDiscoveryEvent) -> None:
        raise NotImplementedError()

    def deregister(self, handler: OnDiscoveryEvent) -> None:
        raise NotImplementedError()

    def get_handlers(self) -> list[OnDiscoveryEvent]:
        raise NotImplementedError()


class DefaultDiscoverer(Discoverer):

    def __init__(self, sender: Sender, receiver: Receiver) -> None:
        self._sender = sender
        self._receiver = receiver
        self._group: Group | None = None
        self._matcher: ServiceMatcher | None = None
        self._cache: dict[str, ServiceInfo] = {}
        self._handlers: list[OnDiscoveryEvent] = []

    def __enter__(self) -> Discoverer:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, address: str, group: Group, query: ServiceQuery | None = None) -> None:
        self._group = group
        if query:
            self._matcher = ServiceMatcher(query)
        self._sender.start(GroupAccess(address, group.query()))
        self._receiver.register(self._handle_message)
        self._receiver.start(GroupAccess(address, group.hello()))

    def stop(self) -> None:
        self._group = None
        self._sender.stop()
        self._receiver.stop()

    def discover(self, query: ServiceQuery | None = None) -> None:
        if self._group:
            if query:
                self._matcher = ServiceMatcher(query)
            if self._matcher:
                self._sender.send(self._matcher.query)
                log.info('Service discovery initiated', query=self._matcher.query, group=self._group)
        else:
            log.warning('Cannot discover services, discoverer not started', query=query)

    def get_services(self) -> dict[str, ServiceInfo]:
        return self._cache.copy()

    def register(self, handler: OnDiscoveryEvent) -> None:
        self._handlers.append(handler)

    def deregister(self, handler: OnDiscoveryEvent) -> None:
        self._handlers.remove(handler)

    def get_handlers(self) -> list[OnDiscoveryEvent]:
        return self._handlers.copy()

    def _handle_message(self, message: dict[str, Any]) -> None:
        try:
            service = ServiceInfo(**message)
            self._handle_service(service)
        except Exception as error:
            log.warn('Failed to handle received message', data=message, error=error)

    def _handle_service(self, service: ServiceInfo) -> None:
        if self._matcher and self._matcher.matches(service):
            cached = self._cache.get(service.name)

            if event := self._create_event(cached, service):
                self._handle_event(event)

    def _create_event(self, cached: ServiceInfo | None, service: ServiceInfo) -> DiscoveryEvent | None:
        if cached:
            if cached != service:
                log.info('Service updated', old_service=cached, new_service=service)
                return DiscoveryEvent(service, DiscoveryEventType.UPDATED)
            else:
                return None
        else:
            log.info('Service discovered', service=service)
            return DiscoveryEvent(service, DiscoveryEventType.DISCOVERED)

    def _handle_event(self, event: DiscoveryEvent) -> None:
        service = event.service
        self._cache[service.name] = service
        for callback in self._handlers:
            try:
                callback(event)
            except Exception as error:
                log.warn('Error in event handler execution', event=event, error=error)

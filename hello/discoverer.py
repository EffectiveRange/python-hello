# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from logging import INFO, DEBUG
from typing import Any, Protocol
from uuid import UUID

from common_utility import IReusableTimer
from context_logger import get_logger

from hello import Group, ServiceQuery, Sender, Receiver, ServiceInfo, ServiceMatcher, AbstractScheduler

log = get_logger('Discoverer')


class DiscoveryEventType(Enum):
    DISCOVERED = 'discovered'
    UPDATED = 'updated'


@dataclass
class DiscoveryEvent:
    group: Group
    query: ServiceQuery
    service: ServiceInfo
    type: DiscoveryEventType


class OnDiscoveryEvent(Protocol):
    def __call__(self, event: DiscoveryEvent) -> None: ...


class Discoverer:

    def start(self, group: Group, query: ServiceQuery | None = None) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def discover(self, query: ServiceQuery | None = None, log_level: int = INFO) -> None:
        raise NotImplementedError()

    def register(self, handler: OnDiscoveryEvent) -> None:
        raise NotImplementedError()

    def deregister(self, handler: OnDiscoveryEvent) -> None:
        raise NotImplementedError()

    def get_services(self) -> dict[UUID, ServiceInfo]:
        raise NotImplementedError()


class DefaultDiscoverer(Discoverer):

    def __init__(self, sender: Sender, receiver: Receiver, max_workers: int = 8) -> None:
        self._sender = sender
        self._receiver = receiver
        self._group: Group | None = None
        self._matcher: ServiceMatcher | None = None
        self._services: dict[UUID, ServiceInfo] = {}
        self._handlers: list[OnDiscoveryEvent] = []
        self._handler_executor = ThreadPoolExecutor(max_workers=max_workers)

    def __enter__(self) -> Discoverer:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, group: Group, query: ServiceQuery | None = None) -> None:
        self._group = group
        if query:
            self._matcher = ServiceMatcher(query)
        self._sender.start(group.query())
        self._receiver.register(self._handle_message)
        self._receiver.start(group.hello())
        log.info('Discoverer started', group=self._group, query=query)

    def stop(self) -> None:
        self._group = None
        self._matcher = None
        self._sender.stop()
        self._receiver.deregister(self._handle_message)
        self._receiver.stop()
        log.info('Discoverer stopped')

    def discover(self, query: ServiceQuery | None = None, log_level: int = INFO) -> None:
        if self._group:
            if query:
                self._matcher = ServiceMatcher(query)
            if self._matcher:
                self._sender.send(self._matcher.query)
                log.log(log_level, 'Service discovery initiated', group=self._group, query=self._matcher.query)
            else:
                log.warning('Cannot discover services, no query provided', group=self._group)
        else:
            log.warning('Cannot discover services, discoverer not started', query=query)

    def register(self, handler: OnDiscoveryEvent) -> None:
        self._handlers.append(handler)

    def deregister(self, handler: OnDiscoveryEvent) -> None:
        self._handlers.remove(handler)

    def get_services(self) -> dict[UUID, ServiceInfo]:
        return self._services.copy()

    def _handle_message(self, message: dict[str, Any]) -> None:
        if self._group and self._matcher:
            try:
                service = ServiceInfo(UUID(message['uuid']), message['name'], message['role'], message.get('urls', {}))
                log.debug('Service info received', service=service, group=self._group)
                self._handle_service(service, self._group, self._matcher)
            except Exception as error:
                log.warn('Invalid service info received', group=self._group, data=message, error=error)

    def _handle_service(self, service: ServiceInfo, group: Group, matcher: ServiceMatcher) -> None:
        if matcher.matches(service):
            stored = self._services.get(service.uuid)

            if event := self._create_event(group, matcher, stored, service):
                self._handle_event(event)

    def _create_event(self, group: Group, matcher: ServiceMatcher,
                      stored: ServiceInfo | None, service: ServiceInfo) -> DiscoveryEvent | None:
        if stored:
            if stored != service:
                log.info('Service updated', group=group, old_service=stored, new_service=service)
                return DiscoveryEvent(group, matcher.query, service, DiscoveryEventType.UPDATED)
            else:
                log.debug('Service unchanged', group=group, service=service)
                return None
        else:
            log.info('New service discovered', group=group, service=service)
            return DiscoveryEvent(group, matcher.query, service, DiscoveryEventType.DISCOVERED)

    def _handle_event(self, event: DiscoveryEvent) -> None:
        self._services[event.service.uuid] = event.service

        for handler in self._handlers:
            self._handler_executor.submit(self._execute_handler, handler, event)

    def _execute_handler(self, handler: OnDiscoveryEvent, event: DiscoveryEvent) -> None:
        try:
            handler(event)
        except Exception as error:
            log.warn('Error in event handler execution', event=event, error=error)


class ScheduledDiscoverer(AbstractScheduler[ServiceQuery], Discoverer):

    def __init__(self, discoverer: Discoverer, timer: IReusableTimer) -> None:
        super().__init__(timer)
        self._discoverer = discoverer

    def __enter__(self) -> 'ScheduledDiscoverer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, group: Group, query: ServiceQuery | None = None) -> None:
        self._discoverer.start(group, query)

    def stop(self) -> None:
        super().stop()
        self._discoverer.stop()

    def discover(self, query: ServiceQuery | None = None, log_level: int = INFO) -> None:
        self._discoverer.discover(query, log_level)

    def get_services(self) -> dict[UUID, ServiceInfo]:
        return self._discoverer.get_services()

    def register(self, handler: OnDiscoveryEvent) -> None:
        self._discoverer.register(handler)

    def deregister(self, handler: OnDiscoveryEvent) -> None:
        self._discoverer.deregister(handler)

    def _execute(self, query: ServiceQuery | None = None) -> None:
        self.discover(query, DEBUG)

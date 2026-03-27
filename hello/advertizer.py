# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import random
import time
from logging import INFO, DEBUG
from typing import Any

from common_utility import IReusableTimer
from context_logger import get_logger

from hello import ServiceInfo, Group, Sender, Receiver, ServiceMatcher, ServiceQuery, AbstractScheduler

log = get_logger('Advertizer')


class Advertizer:

    def start(self, group: Group, info: ServiceInfo | None = None) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def advertise(self, info: ServiceInfo | None = None, log_level: int = INFO) -> None:
        raise NotImplementedError()


class DefaultAdvertizer(Advertizer):

    def __init__(self, sender: Sender) -> None:
        self._sender = sender
        self._group: Group | None = None
        self._info: ServiceInfo | None = None

    def __enter__(self) -> Advertizer:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, group: Group, info: ServiceInfo | None = None) -> None:
        self._sender.start(group.hello())
        self._group = group
        self._info = info
        log.info('Advertizer started', group=self._group, service=self._info)

    def stop(self) -> None:
        self._group = None
        self._info = None
        self._sender.stop()
        log.info('Advertizer stopped')

    def advertise(self, info: ServiceInfo | None = None, log_level: int = INFO) -> None:
        if self._group:
            if info:
                self._info = info
            if self._info:
                self._sender.send(self._info)
                log.log(log_level, 'Service advertised', service=self._info, group=self._group)
            else:
                log.warning('Cannot advertise service, no service info provided', group=self._group)
        else:
            log.warning('Cannot advertise service, advertizer not started', service=info)


class RespondingAdvertizer(DefaultAdvertizer):

    def __init__(self, sender: Sender, receiver: Receiver, max_response_delay: float = 0.1) -> None:
        super().__init__(sender)
        self._receiver = receiver
        self._max_delay = max_response_delay

    def start(self, group: Group, info: ServiceInfo | None = None) -> None:
        super().start(group, info)
        self._receiver.start(group.query())
        self._receiver.register(self._handle_message)

    def stop(self) -> None:
        self._receiver.deregister(self._handle_message)
        self._receiver.stop()
        super().stop()

    def _handle_message(self, message: dict[str, Any]) -> None:
        if self._info:
            try:
                query = ServiceQuery(**message)
                matcher = ServiceMatcher(query)
                log.debug('Service query received', group=self._group, query=query)
                self._handle_query(matcher, self._info)
            except Exception as error:
                log.warning('Invalid service query received', group=self._group, received=message, error=error)

    def _handle_query(self, matcher: ServiceMatcher, info: ServiceInfo) -> None:
        if matcher.matches(info):
            delay = round(self._max_delay * random.random(), 3)
            log.info('Responding to query', group=self._group, query=matcher.query, service=info, delay=delay)
            time.sleep(delay)
            self.advertise(info)


class ScheduledAdvertizer(AbstractScheduler[ServiceInfo], Advertizer):

    def __init__(self, advertizer: Advertizer, timer: IReusableTimer) -> None:
        super().__init__(timer)
        self._advertizer = advertizer

    def __enter__(self) -> 'ScheduledAdvertizer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, group: Group, info: ServiceInfo | None = None) -> None:
        self._advertizer.start(group, info)

    def stop(self) -> None:
        super().stop()
        self._advertizer.stop()

    def advertise(self, info: ServiceInfo | None = None, log_level: int = INFO) -> None:
        self._advertizer.advertise(info, log_level)

    def _execute(self, info: ServiceInfo | None = None) -> None:
        self.advertise(info, DEBUG)

import random
import time
from typing import Any

from common_utility import IReusableTimer
from context_logger import get_logger

from hello import ServiceInfo, Group, Sender, GroupAccess, Receiver, ServiceMatcher, ServiceQuery

log = get_logger('Advertizer')


class Advertizer:

    def start(self, address: str, group: Group, info: ServiceInfo | None = None) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def advertise(self, info: ServiceInfo | None = None) -> None:
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

    def start(self, address: str, group: Group, info: ServiceInfo | None = None) -> None:
        self._sender.start(GroupAccess(address, group.hello()))
        self._group = group
        self._info = info

    def stop(self) -> None:
        self._group = None
        self._sender.stop()

    def advertise(self, info: ServiceInfo | None = None) -> None:
        if self._group:
            if info:
                self._info = info
            if self._info:
                self._sender.send(self._info)
                log.info('Service advertised', service=self._info, group=self._group)
        else:
            log.warning('Cannot advertise service, advertizer not started', service=info)


class RespondingAdvertizer(DefaultAdvertizer):

    def __init__(self, sender: Sender, receiver: Receiver, max_response_delay: float = 0.1) -> None:
        super().__init__(sender)
        self._receiver = receiver
        self._max_delay = max_response_delay

    def start(self, address: str, group: Group, info: ServiceInfo | None = None) -> None:
        super().start(address, group, info)
        self._receiver.start(GroupAccess(address, group.query()))
        self._receiver.register(self._handle_message)

    def stop(self) -> None:
        super().stop()
        self._receiver.stop()

    def _handle_message(self, message: dict[str, Any]) -> None:
        if self._info:
            try:
                query = ServiceQuery(**message)
                log.debug('Query received', group=self._group, query=query)
                self._handle_query(query, self._info)
            except Exception as error:
                log.warning('Invalid query message received', group=self._group, received=message, error=error)

    def _handle_query(self, query: ServiceQuery, info: ServiceInfo) -> None:
        matcher = ServiceMatcher(query)
        if matcher and matcher.matches(info):
            delay = round(self._max_delay * random.random(), 3)
            log.info('Responding to query', group=self._group, query=matcher.query, service=info, delay=delay)
            time.sleep(delay)
            self.advertise(info)


class ScheduledAdvertizer(Advertizer):

    def schedule(self, info: ServiceInfo | None = None, interval: float = 10, one_shot: bool = False) -> None:
        raise NotImplementedError()


class DefaultScheduledAdvertizer(ScheduledAdvertizer):

    def __init__(self, advertizer: Advertizer, timer: IReusableTimer) -> None:
        self._advertizer = advertizer
        self._timer = timer

    def __enter__(self) -> ScheduledAdvertizer:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, address: str, group: Group, info: ServiceInfo | None = None) -> None:
        self._advertizer.start(address, group, info)

    def stop(self) -> None:
        self._timer.cancel()
        self._advertizer.stop()

    def advertise(self, info: ServiceInfo | None = None) -> None:
        self._advertizer.advertise(info)

    def schedule(self, info: ServiceInfo | None = None, interval: float = 60, one_shot: bool = False) -> None:
        if one_shot:
            self._timer.start(interval, self.advertise, [info])
            log.info('One-shot service advertisement scheduled', service=info, interval=interval)
        else:
            self._timer.start(interval, self._advertise_and_restart, [info])
            log.info('Periodic service advertisement scheduled', service=info, interval=interval)

    def _advertise_and_restart(self, info: ServiceInfo | None = None) -> None:
        self.advertise(info)
        self._timer.restart()

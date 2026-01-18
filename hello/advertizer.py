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
                self._sender.send(info)
                log.info('Service advertised', service=self._info, group=self._group)
        else:
            log.warning('Cannot advertise service, advertizer not started', service=info)


class RespondingAdvertizer(DefaultAdvertizer):

    def __init__(self, sender: Sender, receiver: Receiver) -> None:
        super().__init__(sender)
        self._receiver = receiver

    def start(self, address: str, group: Group, info: ServiceInfo | None = None) -> None:
        super().start(address, group, info)
        self._receiver.start(GroupAccess(address, group.query()))
        self._receiver.register(self._handle_query)

    def stop(self) -> None:
        super().stop()
        self._receiver.stop()

    def _handle_query(self, data: dict[str, str]) -> None:
        if self._info:
            matcher: ServiceMatcher | None = None

            try:
                query = ServiceQuery(**data)
                matcher = ServiceMatcher(query)
                log.debug('Hail received', group=self._group, query=query)
            except Exception as error:
                log.warning('Invalid query message received', group=self._group, received=data, error=error)

            if matcher and matcher.matches(self._info):
                log.info('Hail matches service', group=self._group, query=matcher.query, service=self._info)
                self.advertise(self._info)


class ScheduledAdvertizer(Advertizer):

    def schedule(self, info: ServiceInfo, interval: float, one_shot: bool = False) -> None:
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

    def schedule(self, info: ServiceInfo, interval: float, one_shot: bool = False) -> None:
        if one_shot:
            self._timer.start(interval, self.advertise, [info])
            log.info('One-shot service advertisement scheduled', service=info, interval=interval)
        else:
            def periodic_advertise() -> None:
                self.advertise(info)
                self._timer.restart()

            self._timer.start(interval, periodic_advertise)
            log.info('Periodic service advertisement scheduled', service=info, interval=interval)

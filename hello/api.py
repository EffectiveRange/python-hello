from typing import Any

from common_utility import ReusableTimer
from zmq import Context

from hello import Advertizer, Discoverer, RadioSender, DishReceiver, DefaultAdvertizer, DefaultDiscoverer, \
    ScheduledAdvertizer, RespondingAdvertizer, DefaultScheduledAdvertizer


class Hello:

    def default_advertizer(self, respond: bool = True, delay: float = 0.1) -> Advertizer:
        raise NotImplementedError()

    def scheduled_advertizer(self, respond: bool = True, delay: float = 0.1) -> ScheduledAdvertizer:
        raise NotImplementedError()

    def discoverer(self) -> Discoverer:
        raise NotImplementedError()


class DefaultHello(Hello):

    def __init__(self, context: Context[Any] | None = None, max_workers: int = 1, poll_timeout: float = 0.1) -> None:
        self._context = context if context else Context()
        self._max_workers = max_workers
        self._poll_timeout = poll_timeout

    def default_advertizer(self, respond: bool = True, delay: float = 0.1) -> Advertizer:
        sender = RadioSender(self._context)
        if respond:
            receiver = DishReceiver(self._context, self._max_workers, self._poll_timeout)
            return RespondingAdvertizer(sender, receiver, delay)
        else:
            return DefaultAdvertizer(sender)

    def scheduled_advertizer(self, respond: bool = True, delay: float = 0.1) -> ScheduledAdvertizer:
        advertizer = self.default_advertizer(respond, delay)
        return DefaultScheduledAdvertizer(advertizer, ReusableTimer())

    def discoverer(self) -> Discoverer:
        sender = RadioSender(self._context)
        receiver = DishReceiver(self._context, self._max_workers, self._poll_timeout)
        return DefaultDiscoverer(sender, receiver)

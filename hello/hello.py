from typing import Any

from common_utility import ReusableTimer, IReusableTimer
from zmq import Context

from hello import Advertizer, Discoverer, RadioSender, DishReceiver, DefaultAdvertizer, DefaultDiscoverer, \
    ScheduledAdvertizer, RespondingAdvertizer, DefaultScheduledAdvertizer


class Hello:

    def default_advertizer(self, respond: bool = True) -> Advertizer:
        raise NotImplementedError()

    def scheduled_advertizer(self, timer: IReusableTimer | None = None, respond: bool = True) -> ScheduledAdvertizer:
        raise NotImplementedError()

    def discoverer(self) -> Discoverer:
        raise NotImplementedError()


class DefaultHello(Hello):

    def __init__(self, context: Context[Any] | None = None) -> None:
        self._context = context if context else Context()
        self._sender = RadioSender(self._context)
        self._receiver = DishReceiver(self._context)

    def default_advertizer(self, respond: bool = True) -> Advertizer:
        return RespondingAdvertizer(self._sender, self._receiver) if respond else DefaultAdvertizer(self._sender)

    def scheduled_advertizer(self, timer: IReusableTimer | None = None, respond: bool = True) -> ScheduledAdvertizer:
        advertizer = self.default_advertizer(respond)
        reusable_timer = timer if timer else ReusableTimer()
        return DefaultScheduledAdvertizer(advertizer, reusable_timer)

    def discoverer(self) -> Discoverer:
        return DefaultDiscoverer(self._sender, self._receiver)

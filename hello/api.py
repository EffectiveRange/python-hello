from dataclasses import dataclass
from typing import Any

from common_utility import ReusableTimer
from zmq import Context

from hello import RadioSender, DishReceiver, DefaultAdvertizer, DefaultDiscoverer, \
    RespondingAdvertizer, ScheduledAdvertizer, ScheduledDiscoverer


@dataclass
class HelloConfig:
    context: Context[Any] = Context()
    receiver_max_workers: int = 1
    receiver_poll_timeout: float = 0.1
    advertizer_responder: bool = True
    advertizer_max_delay: float = 0.1


class Hello(object):

    @classmethod
    def default_config(cls) -> HelloConfig:
        return HelloConfig()

    @classmethod
    def default_advertizer(cls, config: HelloConfig) -> DefaultAdvertizer:
        sender = RadioSender(config.context)
        if config.advertizer_responder:
            receiver = DishReceiver(config.context, config.receiver_max_workers, config.receiver_poll_timeout)
            return RespondingAdvertizer(sender, receiver, config.advertizer_max_delay)
        else:
            return DefaultAdvertizer(sender)

    @classmethod
    def scheduled_advertizer(cls, config: HelloConfig) -> ScheduledAdvertizer:
        advertizer = cls.default_advertizer(config)
        return ScheduledAdvertizer(advertizer, ReusableTimer())

    @classmethod
    def default_discoverer(cls, config: HelloConfig) -> DefaultDiscoverer:
        sender = RadioSender(config.context)
        receiver = DishReceiver(config.context, config.receiver_max_workers, config.receiver_poll_timeout)
        return DefaultDiscoverer(sender, receiver)

    @classmethod
    def scheduled_discoverer(cls, config: HelloConfig) -> ScheduledDiscoverer:
        discoverer = cls.default_discoverer(config)
        return ScheduledDiscoverer(discoverer, ReusableTimer())

    @classmethod
    def builder(cls) -> 'HelloBuilder':
        return HelloBuilder()


class AdvertizerBuilder(object):

    def __init__(self, config: HelloConfig) -> None:
        self._config = config

    def default(self) -> DefaultAdvertizer:
        return Hello.default_advertizer(self._config)

    def scheduled(self) -> ScheduledAdvertizer:
        return Hello.scheduled_advertizer(self._config)


class DiscovererBuilder(object):

    def __init__(self, config: HelloConfig) -> None:
        self._config = config

    def default(self) -> DefaultDiscoverer:
        return Hello.default_discoverer(self._config)

    def scheduled(self) -> ScheduledDiscoverer:
        return Hello.scheduled_discoverer(self._config)


class HelloBuilder(object):

    def __init__(self) -> None:
        self._config = Hello.default_config()

    def config(self, config: HelloConfig) -> 'HelloBuilder':
        self._config = config
        return self

    def advertizer(self) -> AdvertizerBuilder:
        return AdvertizerBuilder(self._config)

    def discoverer(self) -> DiscovererBuilder:
        return DiscovererBuilder(self._config)

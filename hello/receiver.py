# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Protocol

from context_logger import get_logger
from zmq import DISH, Poller, POLLIN, Context

from hello import PrefixedGroup

log = get_logger('Receiver')


class OnMessage(Protocol):
    def __call__(self, message: dict[str, Any]) -> None: ...


class Receiver:

    def start(self, group: PrefixedGroup) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def register(self, handler: OnMessage) -> None:
        raise NotImplementedError()

    def deregister(self, handler: OnMessage) -> None:
        raise NotImplementedError()

    def get_handlers(self) -> list[OnMessage]:
        raise NotImplementedError()


class DishReceiver(Receiver):

    def __init__(self, context: Context[Any], max_workers: int = 8, poll_timeout: float = 0.1) -> None:
        self._context = context
        self._dish = self._context.socket(DISH)
        self._poller = Poller()
        self._loop_executor = ThreadPoolExecutor(max_workers=1)
        self._handler_executor = ThreadPoolExecutor(max_workers=max_workers)
        self._poll_timeout = int(poll_timeout * 1000)
        self._group: str | None = None
        self._handlers: list[OnMessage] = []

    def __enter__(self) -> Receiver:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, group: PrefixedGroup) -> None:
        try:
            if self._group:
                raise RuntimeError('Receiver already started')
            self._poller.register(self._dish, POLLIN)
            self._dish.bind(group.url)
            self._dish.join(group.name)
            self._group = group.name
            self._loop_executor.submit(self._receive_loop)
            log.debug('Receiver started', url=group.url, group=group.name)
        except Exception as error:
            log.error('Failed to start receiver', url=group.url, group=group.name, error=error)
            raise error

    def stop(self) -> None:
        try:
            self._group = None
            self._loop_executor.shutdown()
            self._dish.close()
            log.debug('Receiver stopped')
        except Exception as error:
            log.error('Failed to stop receiver', error=error)
            raise error

    def register(self, handler: OnMessage) -> None:
        self._handlers.append(handler)

    def deregister(self, handler: OnMessage) -> None:
        self._handlers.remove(handler)

    def get_handlers(self) -> list[OnMessage]:
        return self._handlers.copy()

    def _receive_loop(self) -> None:
        while self._group:
            try:
                sockets = dict(self._poller.poll(timeout=self._poll_timeout))
                if self._dish in sockets and sockets[self._dish] == POLLIN:
                    message = self._dish.recv_json()
                    self._handle_message(message)
            except Exception as error:
                log.error('Failed to receive message', group=self._group, error=error)

    def _handle_message(self, message: dict[str, Any]) -> None:
        log.debug('Message received', data=message, group=self._group)
        for handler in self._handlers:
            self._handler_executor.submit(self._execute_handler, handler, message)

    def _execute_handler(self, handler: OnMessage, message: dict[str, Any]) -> None:
        try:
            handler(message)
        except Exception as error:
            log.warn('Error in message handler execution', data=message, group=self._group, error=error)

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Protocol

from context_logger import get_logger
from zmq import DISH, Poller, POLLIN, POLLOUT, Context

from hello import GroupAccess

log = get_logger('Receiver')


class OnMessage(Protocol):
    def __call__(self, message: dict[str, Any]) -> None: ...


class Receiver:

    def start(self, source: GroupAccess) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def register(self, callback: OnMessage) -> None:
        raise NotImplementedError()

    def deregister(self, callback: OnMessage) -> None:
        raise NotImplementedError()


class DishReceiver(Receiver):

    def __init__(self, context: Context[Any], max_workers: int = 1, poll_timeout: float = 0.1) -> None:
        self._context = context
        self._dish = self._context.socket(DISH)
        self._poller = Poller()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._poll_timeout = int(poll_timeout * 1000)
        self._group: str | None = None
        self._callbacks: list[OnMessage] = []

    def __enter__(self) -> Receiver:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, source: GroupAccess) -> None:
        try:
            if self._group:
                raise RuntimeError('Receiver already started')
            self._poller.register(self._dish, POLLIN)
            self._dish.bind(source.access_url)
            self._dish.join(source.full_group)
            self._group = source.full_group
            self._executor.submit(self._handle_messages)
            log.debug('Receiver started', address=source.access_url, group=source.full_group)
        except Exception as error:
            log.error('Failed to start receiver', address=source.access_url, group=source.full_group, error=error)
            raise error

    def stop(self) -> None:
        try:
            self._group = None
            self._poller.register(self._dish, POLLOUT)
            self._executor.shutdown()
            self._dish.close()
            log.debug('Receiver stopped')
        except Exception as error:
            log.error('Failed to stop receiver', error=error)
            raise error

    def register(self, callback: OnMessage) -> None:
        self._callbacks.append(callback)

    def deregister(self, callback: OnMessage) -> None:
        self._callbacks.remove(callback)

    def _handle_messages(self) -> None:
        while self._group:
            sockets = dict(self._poller.poll(timeout=self._poll_timeout))
            if self._dish in sockets and sockets[self._dish] == POLLIN:
                try:
                    data = self._dish.recv_json()
                    log.debug('Message received', data=data, group=self._group)
                    self._handle_message(data)
                except Exception as error:
                    log.error('Failed to receive message', group=self._group, error=error)

    def _handle_message(self, message: dict[str, Any]) -> None:
        for callback in self._callbacks:
            try:
                callback(message)
            except Exception as error:
                log.warn('Error in callback execution', data=message, group=self._group, error=error)

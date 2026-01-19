from typing import Any, cast

from context_logger import get_logger
from zmq import Context, RADIO, Socket

from hello import GroupAccess

log = get_logger('Sender')


class Sender:

    def start(self, target: GroupAccess) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def send(self, data: object) -> None:
        raise NotImplementedError()


class RadioSender(Sender):

    def __init__(self, context: Context[Any]) -> None:
        self._context = context
        self._radio: Socket[bytes] = self._context.socket(RADIO)
        self._group: str | None = None

    def __enter__(self) -> Sender:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self, target: GroupAccess) -> None:
        try:
            if self._group:
                raise RuntimeError('Sender already started')
            self._radio.connect(target.access_url)
            self._group = target.full_group
            log.debug('Sender started', address=target.access_url, group=target.full_group)
        except Exception as error:
            log.error('Failed to start sender', address=target.access_url, group=target.full_group, error=error)
            raise error

    def stop(self) -> None:
        try:
            self._group = None
            self._radio.close()
            log.debug('Sender stopped')
        except Exception as error:
            log.error('Failed to stop sender', error=error)
            raise error

    def send(self, data: Any) -> None:
        if self._group:
            if data := self._convert_to_dict(data):
                self._send_json(data)
            else:
                log.warning('Unsupported message type', data=data, group=self._group)
        else:
            log.warning('Cannot send message, sender not started', data=data)

    def _convert_to_dict(self, data: Any) -> dict[str, Any] | None:
        if isinstance(data, dict):
            return data
        elif hasattr(data, '__dict__'):
            return cast(dict[str, Any], data.__dict__)
        return None

    def _send_json(self, data: dict[str, Any]) -> None:
        try:
            self._radio.send_json(data, group=self._group)
            log.debug('Message sent', data=data, group=self._group)
        except Exception as error:
            log.error('Failed to send message', data=data, group=self._group, error=error)

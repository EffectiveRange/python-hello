from signal import signal, SIGINT, SIGTERM
from threading import Event
from typing import Any


def setup_shutdown() -> Event:
    shutdown_event = Event()

    def handler(signum: int, frame: Any) -> None:
        shutdown_event.set()

    signal(SIGINT, handler)
    signal(SIGTERM, handler)

    return shutdown_event

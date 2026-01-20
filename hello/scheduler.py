from typing import TypeVar, Generic, Any

from common_utility import IReusableTimer
from context_logger import get_logger

log = get_logger('Scheduler')

T = TypeVar('T')


class Scheduler(Generic[T]):

    def stop(self) -> None:
        raise NotImplementedError()

    def schedule(self, data: T | None = None, interval: float = 60, one_shot: bool = False) -> None:
        raise NotImplementedError()


class DefaultScheduler(Scheduler[T]):

    def __init__(self, timer: IReusableTimer) -> None:
        self._timer = timer

    def __enter__(self) -> Scheduler[T]:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def stop(self) -> None:
        self._timer.cancel()

    def schedule(self, data: T | None = None, interval: float = 60, one_shot: bool = False) -> None:
        if one_shot:
            self._timer.start(interval, self._execute, [data])
            log.info('One-shot execution scheduled', data=data, interval=interval)
        else:
            self._timer.start(interval, self._execute_and_restart, [data])
            log.info('Periodic execution scheduled', data=data, interval=interval)

    def _execute(self, data: T | None = None) -> None:
        raise NotImplementedError()

    def _execute_and_restart(self, data: T | None = None) -> None:
        self._execute(data)
        self._timer.restart()

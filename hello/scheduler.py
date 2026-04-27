# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from typing import TypeVar, Generic, Any

from common_utility import IReusableTimer
from context_logger import get_logger

T = TypeVar('T')


class Scheduler(Generic[T]):

    def schedule_one_shot(self, data: T | None = None, interval: float | None = None) -> None:
        raise NotImplementedError()

    def schedule_periodic(self, data: T | None = None, interval: float | None = None) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()


class AbstractScheduler(Scheduler[T]):

    def __init__(self, timer: IReusableTimer, interval: float = 60) -> None:
        self._timer = timer
        self._interval = interval
        self.log = get_logger(type(self).__name__)

    def __enter__(self) -> Scheduler[T]:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def schedule_one_shot(self, data: T | None = None, interval: float | None = None) -> None:
        resolved_interval: float = self._interval if interval is None else interval
        self._timer.start(resolved_interval, self._safe_execute, [data])
        self.log.info('One-shot execution scheduled', data=data, interval=resolved_interval)

    def schedule_periodic(self, data: T | None = None, interval: float | None = None) -> None:
        resolved_interval: float = self._interval if interval is None else interval
        self._timer.start(resolved_interval, self._execute_and_restart, [data])
        self.log.info('Periodic execution scheduled', data=data, interval=resolved_interval)

    def stop(self) -> None:
        self._timer.cancel()

    def _execute(self, data: T | None = None) -> None:
        raise NotImplementedError()

    def _execute_and_restart(self, data: T | None = None) -> None:
        self._safe_execute(data)
        self._timer.restart()

    def _safe_execute(self, data: T | None = None) -> None:
        try:
            self._execute(data)
        except Exception as e:
            self.log.error('Error during scheduled execution', error=e, data=data)

import unittest
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import IReusableTimer
from context_logger import setup_logging

from hello import AbstractScheduler


class AbstractSchedulerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_stops_timer_on_exit(self):
        # Given
        timer = MagicMock(spec=IReusableTimer)

        with TestScheduler(timer):
            # When
            pass

        # Then
        timer.cancel.assert_called_once()

    def test_stops_timer_when_stopped(self):
        # Given
        timer = MagicMock(spec=IReusableTimer)
        scheduler = TestScheduler(timer)

        # When
        scheduler.stop()

        # Then
        timer.cancel.assert_called_once()

    def test_schedules_execution_once(self):
        # Given
        timer = MagicMock(spec=IReusableTimer)
        scheduler = TestScheduler(timer)
        data = MagicMock()

        # When
        scheduler.schedule_one_shot(data, 60)

        # Then
        timer.start.assert_called_once_with(60, scheduler._execute, [data])

    def test_schedules_execution_once_with_default_interval(self):
        # Given
        timer = MagicMock(spec=IReusableTimer)
        scheduler = TestScheduler(timer, 10)
        data = MagicMock()

        # When
        scheduler.schedule_one_shot(data)

        # Then
        timer.start.assert_called_once_with(10, scheduler._execute, [data])

    def test_schedules_execution_periodically(self):
        # Given
        timer = MagicMock(spec=IReusableTimer)
        scheduler = TestScheduler(timer)
        data = MagicMock()

        # When
        scheduler.schedule_periodic(data, 60)

        # Then
        timer.start.assert_called_once_with(60, scheduler._execute_and_restart, [data])

    def test_schedules_execution_periodically_with_default_interval(self):
        # Given
        timer = MagicMock(spec=IReusableTimer)
        scheduler = TestScheduler(timer, 10)
        data = MagicMock()

        # When
        scheduler.schedule_periodic(data)

        # Then
        timer.start.assert_called_once_with(10, scheduler._execute_and_restart, [data])

    def test_execute_and_restart_restarts_timer(self):
        # Given
        timer = MagicMock(spec=IReusableTimer)
        scheduler = TestScheduler(timer)
        data = MagicMock()

        # When
        scheduler._execute_and_restart(data)

        # Then
        timer.restart.assert_called_once()


class TestScheduler(AbstractScheduler[Any]):

    def __init__(self, timer: IReusableTimer, interval: float = 0) -> None:
        super().__init__(timer, interval)

    def _execute(self, data: Any | None = None) -> None:
        pass


if __name__ == '__main__':
    unittest.main()

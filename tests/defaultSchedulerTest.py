import unittest
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import IReusableTimer
from context_logger import setup_logging

from hello import DefaultScheduler


class DefaultSchedulerDiscovererTest(TestCase):

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
        scheduler.schedule(data, 60, True)

        # Then
        timer.start.assert_called_once_with(60, scheduler._execute, [data])

    def test_schedules_periodic_discover(self):
        # Given
        timer = MagicMock(spec=IReusableTimer)
        scheduler = TestScheduler(timer)
        data = MagicMock()

        # When
        scheduler.schedule(data, 60, False)

        # Then
        timer.start.assert_called_once_with(60, scheduler._execute_and_restart, [data])

    def test_execute_and_restart_restarts_timer(self):
        # Given
        timer = MagicMock(spec=IReusableTimer)
        scheduler = TestScheduler(timer)
        data = MagicMock()

        # When
        scheduler._execute_and_restart(data)

        # Then
        timer.restart.assert_called_once()


class TestScheduler(DefaultScheduler[Any]):

    def __init__(self, timer: IReusableTimer) -> None:
        super().__init__(timer)

    def _execute(self, data: Any | None = None) -> None:
        pass


if __name__ == '__main__':
    unittest.main()

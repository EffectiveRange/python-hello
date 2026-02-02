import unittest
from unittest import TestCase
from unittest.mock import MagicMock
from uuid import uuid4

from common_utility import IReusableTimer
from context_logger import setup_logging

from hello import ServiceInfo, Group, ScheduledAdvertizer, Advertizer

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_INFO = ServiceInfo(uuid4(), 'test-service', 'test-role', {'test': 'http://localhost:8080'})


class ScheduledAdvertizerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_stops_timer_and_advertizer_on_exit(self):
        # Given
        advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)

        with ScheduledAdvertizer(advertizer, timer) as scheduled_advertizer:
            scheduled_advertizer.start(GROUP)

            # When

        # Then
        timer.cancel.assert_called_once()
        advertizer.stop.assert_called_once()

    def test_stops_timer_and_advertizer_when_stopped(self):
        # Given
        advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_advertizer = ScheduledAdvertizer(advertizer, timer)
        scheduled_advertizer.start(GROUP)

        # When
        scheduled_advertizer.stop()

        # Then
        timer.cancel.assert_called_once()
        advertizer.stop.assert_called_once()

    def test_starts_advertizer_when_started(self):
        # Given
        advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_advertizer = ScheduledAdvertizer(advertizer, timer)

        # When
        scheduled_advertizer.start(GROUP, SERVICE_INFO)

        # Then
        advertizer.start.assert_called_once_with(GROUP, SERVICE_INFO)

    def test_sends_service_info(self):
        # Given
        advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_advertizer = ScheduledAdvertizer(advertizer, timer)

        # When
        scheduled_advertizer.advertise(SERVICE_INFO)

        # Then
        advertizer.advertise.assert_called_once_with(SERVICE_INFO)

    def test_schedules_advertise_once(self):
        # Given
        advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_advertizer = ScheduledAdvertizer(advertizer, timer)
        scheduled_advertizer.start(GROUP)

        # When
        scheduled_advertizer.schedule(SERVICE_INFO, 60, True)

        # Then
        timer.start.assert_called_once_with(60, scheduled_advertizer._execute, [SERVICE_INFO])

    def test_schedules_periodic_advertise(self):
        # Given
        advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_advertizer = ScheduledAdvertizer(advertizer, timer)
        scheduled_advertizer.start(GROUP)

        # When
        scheduled_advertizer.schedule(SERVICE_INFO, 60, False)

        # Then
        timer.start.assert_called_once_with(60, scheduled_advertizer._execute_and_restart, [SERVICE_INFO])

    def test_execute_and_restart_calls_advertise_and_restarts_timer(self):
        # Given
        advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_advertizer = ScheduledAdvertizer(advertizer, timer)
        scheduled_advertizer.start(GROUP)

        # When
        scheduled_advertizer._execute_and_restart(SERVICE_INFO)

        # Then
        advertizer.advertise.assert_called_once_with(SERVICE_INFO)
        timer.restart.assert_called_once()


if __name__ == '__main__':
    unittest.main()

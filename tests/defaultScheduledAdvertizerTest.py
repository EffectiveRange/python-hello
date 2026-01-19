import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import IReusableTimer
from context_logger import setup_logging

from hello import ServiceInfo, Group, DefaultScheduledAdvertizer, Advertizer

ACCESS_URL = 'udp://239.0.0.1:5555'
GROUP_NAME = 'test-group'
GROUP = Group(GROUP_NAME)
SERVICE_INFO = ServiceInfo('test-service', 'test-role', 'http://localhost:8080')


class DefaultScheduledAdvertizerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_stops_timer_and_advertizer_on_exit(self):
        # Given
        _advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)

        with DefaultScheduledAdvertizer(_advertizer, timer) as advertizer:
            advertizer.start(ACCESS_URL, GROUP)

            # When

        # Then
        timer.cancel.assert_called_once()
        _advertizer.stop.assert_called_once()

    def test_stops_timer_and_advertizer_when_stopped(self):
        # Given
        _advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        advertizer = DefaultScheduledAdvertizer(_advertizer, timer)
        advertizer.start(ACCESS_URL, GROUP)

        # When
        advertizer.stop()

        # Then
        timer.cancel.assert_called_once()
        _advertizer.stop.assert_called_once()

    def test_starts_advertizer_when_started(self):
        # Given
        _advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        advertizer = DefaultScheduledAdvertizer(_advertizer, timer)

        # When
        advertizer.start(ACCESS_URL, GROUP, SERVICE_INFO)

        # Then
        _advertizer.start.assert_called_once_with(ACCESS_URL, GROUP, SERVICE_INFO)

    def test_sends_service_info(self):
        # Given
        _advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        advertizer = DefaultScheduledAdvertizer(_advertizer, timer)

        # When
        advertizer.advertise(SERVICE_INFO)

        # Then
        _advertizer.advertise.assert_called_once_with(SERVICE_INFO)

    def test_schedules_advertise_once(self):
        # Given
        _advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        advertizer = DefaultScheduledAdvertizer(_advertizer, timer)
        advertizer.start(ACCESS_URL, GROUP)

        # When
        advertizer.schedule(SERVICE_INFO, 60, True)

        # Then
        timer.start.assert_called_once_with(60, advertizer.advertise, [SERVICE_INFO])

    def test_schedules_periodic_advertise(self):
        # Given
        _advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        advertizer = DefaultScheduledAdvertizer(_advertizer, timer)
        advertizer.start(ACCESS_URL, GROUP)

        # When
        advertizer.schedule(SERVICE_INFO, 60, False)

        # Then
        timer.start.assert_called_once_with(60, advertizer._advertise_and_restart, [SERVICE_INFO])

    def test_advertise_and_restart_calls_advertise_and_restarts_timer(self):
        # Given
        _advertizer = MagicMock(spec=Advertizer)
        timer = MagicMock(spec=IReusableTimer)
        advertizer = DefaultScheduledAdvertizer(_advertizer, timer)
        advertizer.start(ACCESS_URL, GROUP)

        # When
        advertizer._advertise_and_restart(SERVICE_INFO)

        # Then
        _advertizer.advertise.assert_called_once_with(SERVICE_INFO)
        timer.restart.assert_called_once()


if __name__ == '__main__':
    unittest.main()

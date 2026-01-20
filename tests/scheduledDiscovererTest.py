import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import IReusableTimer
from context_logger import setup_logging

from hello import ServiceQuery, Group, ScheduledDiscoverer, Discoverer

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_QUERY = ServiceQuery('test-service', 'test-role')


class ScheduledDiscovererTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_stops_timer_and_discoverer_on_exit(self):
        # Given
        _discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)

        with ScheduledDiscoverer(_discoverer, timer) as discoverer:
            discoverer.start(GROUP)

            # When

        # Then
        timer.cancel.assert_called_once()
        _discoverer.stop.assert_called_once()

    def test_stops_timer_and_discoverer_when_stopped(self):
        # Given
        _discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        discoverer = ScheduledDiscoverer(_discoverer, timer)
        discoverer.start(GROUP)

        # When
        discoverer.stop()

        # Then
        timer.cancel.assert_called_once()
        _discoverer.stop.assert_called_once()

    def test_starts_discoverer_when_started(self):
        # Given
        _discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        discoverer = ScheduledDiscoverer(_discoverer, timer)

        # When
        discoverer.start(GROUP, SERVICE_QUERY)

        # Then
        _discoverer.start.assert_called_once_with(GROUP, SERVICE_QUERY)

    def test_sends_service_query(self):
        # Given
        _discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        discoverer = ScheduledDiscoverer(_discoverer, timer)

        # When
        discoverer.discover(SERVICE_QUERY)

        # Then
        _discoverer.discover.assert_called_once_with(SERVICE_QUERY)

    def test_schedules_discover_once(self):
        # Given
        _discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        discoverer = ScheduledDiscoverer(_discoverer, timer)
        discoverer.start(GROUP)

        # When
        discoverer.schedule(SERVICE_QUERY, 60, True)

        # Then
        timer.start.assert_called_once_with(60, discoverer._execute, [SERVICE_QUERY])

    def test_schedules_periodic_discover(self):
        # Given
        _discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        discoverer = ScheduledDiscoverer(_discoverer, timer)
        discoverer.start(GROUP)

        # When
        discoverer.schedule(SERVICE_QUERY, 60, False)

        # Then
        timer.start.assert_called_once_with(60, discoverer._execute_and_restart, [SERVICE_QUERY])

    def test_execute_and_restart_calls_discover_and_restarts_timer(self):
        # Given
        _discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        discoverer = ScheduledDiscoverer(_discoverer, timer)
        discoverer.start(GROUP)

        # When
        discoverer._execute_and_restart(SERVICE_QUERY)

        # Then
        _discoverer.discover.assert_called_once_with(SERVICE_QUERY)
        timer.restart.assert_called_once()


if __name__ == '__main__':
    unittest.main()

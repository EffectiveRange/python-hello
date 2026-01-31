import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import IReusableTimer
from context_logger import setup_logging

from hello import ServiceQuery, Group, ScheduledDiscoverer, Discoverer, OnDiscoveryEvent

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
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)

        with ScheduledDiscoverer(discoverer, timer) as scheduled_discoverer:
            scheduled_discoverer.start(GROUP)

            # When

        # Then
        timer.cancel.assert_called_once()
        discoverer.stop.assert_called_once()

    def test_stops_timer_and_discoverer_when_stopped(self):
        # Given
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_discoverer = ScheduledDiscoverer(discoverer, timer)
        scheduled_discoverer.start(GROUP)

        # When
        scheduled_discoverer.stop()

        # Then
        timer.cancel.assert_called_once()
        discoverer.stop.assert_called_once()

    def test_starts_discoverer_when_started(self):
        # Given
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_discoverer = ScheduledDiscoverer(discoverer, timer)

        # When
        scheduled_discoverer.start(GROUP, SERVICE_QUERY)

        # Then
        discoverer.start.assert_called_once_with(GROUP, SERVICE_QUERY)

    def test_registers_event_handler(self):
        # Given
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_discoverer = ScheduledDiscoverer(discoverer, timer)
        handler = MagicMock(spec=OnDiscoveryEvent)

        # When
        scheduled_discoverer.register(handler)

        # Then
        discoverer.register.assert_called_once_with(handler)

    def test_deregisters_event_handler(self):
        # Given
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_discoverer = ScheduledDiscoverer(discoverer, timer)
        handler = MagicMock(spec=OnDiscoveryEvent)
        scheduled_discoverer.register(handler)

        # When
        scheduled_discoverer.deregister(handler)

        # Then
        discoverer.deregister.assert_called_once_with(handler)

    def test_returns_event_handlers(self):
        # Given
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_discoverer = ScheduledDiscoverer(discoverer, timer)
        scheduled_discoverer.start(GROUP, SERVICE_QUERY)
        handler = MagicMock(spec=OnDiscoveryEvent)
        scheduled_discoverer.register(handler)

        # When
        result = scheduled_discoverer.get_handlers()

        # Then
        self.assertEqual(discoverer.get_handlers(), result)

    def test_sends_service_query(self):
        # Given
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_discoverer = ScheduledDiscoverer(discoverer, timer)

        # When
        scheduled_discoverer.discover(SERVICE_QUERY)

        # Then
        discoverer.discover.assert_called_once_with(SERVICE_QUERY)

    def test_schedules_discover_once(self):
        # Given
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_discoverer = ScheduledDiscoverer(discoverer, timer)
        scheduled_discoverer.start(GROUP)

        # When
        scheduled_discoverer.schedule(SERVICE_QUERY, 60, True)

        # Then
        timer.start.assert_called_once_with(60, scheduled_discoverer._execute, [SERVICE_QUERY])

    def test_schedules_periodic_discover(self):
        # Given
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_discoverer = ScheduledDiscoverer(discoverer, timer)
        scheduled_discoverer.start(GROUP)

        # When
        scheduled_discoverer.schedule(SERVICE_QUERY, 60, False)

        # Then
        timer.start.assert_called_once_with(60, scheduled_discoverer._execute_and_restart, [SERVICE_QUERY])

    def test_execute_and_restart_calls_discover_and_restarts_timer(self):
        # Given
        discoverer = MagicMock(spec=Discoverer)
        timer = MagicMock(spec=IReusableTimer)
        scheduled_discoverer = ScheduledDiscoverer(discoverer, timer)
        scheduled_discoverer.start(GROUP)

        # When
        scheduled_discoverer._execute_and_restart(SERVICE_QUERY)

        # Then
        discoverer.discover.assert_called_once_with(SERVICE_QUERY)
        timer.restart.assert_called_once()


if __name__ == '__main__':
    unittest.main()

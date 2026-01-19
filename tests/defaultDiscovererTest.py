import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging

from hello import ServiceInfo, Group, GroupAccess, \
    ServiceQuery, DefaultDiscoverer, Sender, Receiver, OnDiscoveryEvent, DiscoveryEventType, DiscoveryEvent

ACCESS_URL = 'udp://239.0.0.1:5555'
GROUP_NAME = 'test-group'
GROUP = Group(GROUP_NAME)
SERVICE_QUERY = ServiceQuery('test-.*', 'test-.*')
SERVICE_INFO = ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:8080'})


class DefaultDiscovererTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_stops_sender_and_receiver_on_exit(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)

        with DefaultDiscoverer(sender, receiver) as discoverer:
            discoverer.start(ACCESS_URL, GROUP)

            # When

        # Then
        sender.stop.assert_called_once()
        receiver.stop.assert_called_once()

    def test_stops_sender_and_receiver_when_stopped(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP)

        # When
        discoverer.stop()

        # Then
        sender.stop.assert_called_once()
        receiver.stop.assert_called_once()

    def test_starts_sender_and_receiver_when_started(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)

        # When
        discoverer.start(ACCESS_URL, GROUP)

        # Then
        sender.start.assert_called_once_with(GroupAccess(ACCESS_URL, GROUP.query()))
        receiver.start.assert_called_once_with(GroupAccess(ACCESS_URL, GROUP.hello()))

    def test_registers_event_handler(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        handler = MagicMock(spec=OnDiscoveryEvent)

        # When
        discoverer.register(handler)

        # Then
        self.assertIn(handler, discoverer.get_handlers())

    def test_deregisters_event_handler(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        handler = MagicMock(spec=OnDiscoveryEvent)
        discoverer.register(handler)

        # When
        discoverer.deregister(handler)

        # Then
        self.assertNotIn(handler, discoverer.get_handlers())

    def test_caches_service_and_calls_handler_when_receives_matching_info(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)
        handler = MagicMock(spec=OnDiscoveryEvent)
        discoverer.register(handler)

        # When
        discoverer._handle_message(SERVICE_INFO.__dict__)

        # Then
        self.assertEqual({SERVICE_INFO.name: SERVICE_INFO}, discoverer.get_services())
        handler.assert_called_once_with(DiscoveryEvent(SERVICE_INFO, DiscoveryEventType.DISCOVERED))

    def test_updates_service_and_calls_handler_when_receives_matching_info(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)
        handler = MagicMock(spec=OnDiscoveryEvent)
        discoverer.register(handler)
        discoverer._handle_message(SERVICE_INFO.__dict__)
        handler.reset_mock()
        new_service_info = ServiceInfo(SERVICE_INFO.name, SERVICE_INFO.role, {'test': 'http://localhost:9090'})

        # When
        discoverer._handle_message(new_service_info.__dict__)

        # Then
        self.assertEqual({SERVICE_INFO.name: new_service_info}, discoverer.get_services())
        handler.assert_called_once_with(DiscoveryEvent(new_service_info, DiscoveryEventType.UPDATED))

    def test_does_not_call_handler_when_service_info_not_changed(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)
        handler = MagicMock(spec=OnDiscoveryEvent)
        discoverer.register(handler)
        discoverer._handle_message(SERVICE_INFO.__dict__)
        handler.reset_mock()

        # When
        discoverer._handle_message(SERVICE_INFO.__dict__)

        # Then
        handler.assert_not_called()

    def test_handles_handler_error_gracefully(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)
        handler = MagicMock(spec=OnDiscoveryEvent)
        handler.side_effect = Exception("Handler error")
        discoverer.register(handler)

        # When
        discoverer._handle_message(SERVICE_INFO.__dict__)

        # Then
        self.assertEqual({SERVICE_INFO.name: SERVICE_INFO}, discoverer.get_services())
        handler.assert_called_once_with(DiscoveryEvent(SERVICE_INFO, DiscoveryEventType.DISCOVERED))

    def test_handles_invalid_message_gracefully(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)

        # When
        discoverer._handle_message({'invalid': 'message'})

        # Then
        self.assertEqual({}, discoverer.get_services())

    def test_does_not_cache_service_when_info_not_matching_query(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)

        non_matching_info = ServiceInfo('other-service', 'test-role', {'test': 'http://localhost:8080'})

        # When
        discoverer._handle_message(non_matching_info.__dict__)

        # Then
        self.assertEqual({}, discoverer.get_services())

    def test_does_not_cache_service_when_no_query_set(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP)

        # When
        discoverer._handle_message(SERVICE_INFO.__dict__)

        # Then
        self.assertEqual({}, discoverer.get_services())

    def test_sends_query_when_passed_at_start(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)

        # When
        discoverer.discover()

        # Then
        sender.send.assert_called_once_with(SERVICE_QUERY)

    def test_sends_query_when_passed_at_discover(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP)

        # When
        discoverer.discover(SERVICE_QUERY)

        # Then
        sender.send.assert_called_once_with(SERVICE_QUERY)

    def test_sends_last_query_when_passed_at_start_and_at_discover(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP, ServiceQuery('other-.*', 'test-.*'))

        # When
        discoverer.discover(SERVICE_QUERY)

        # Then
        sender.send.assert_called_once_with(SERVICE_QUERY)

    def test_does_not_send_query_when_no_query_provided(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(ACCESS_URL, GROUP)

        # When
        discoverer.discover()

        # Then
        sender.send.assert_not_called()

    def test_does_not_send_query_when_not_started(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)

        # When
        discoverer.discover(SERVICE_QUERY)

        # Then
        sender.send.assert_not_called()


if __name__ == '__main__':
    unittest.main()

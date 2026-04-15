import unittest
from unittest import TestCase
from unittest.mock import MagicMock
from uuid import uuid4

from context_logger import setup_logging
from test_utility import wait_for_assertion

from hello import Service, Group, ServiceQuery, DefaultDiscoverer, Sender, Receiver, OnDiscoveryEvent, \
    DiscoveryEventType, DiscoveryEvent

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_QUERY = ServiceQuery('test-.*', 'test-.*')
SERVICE = Service(uuid4(), 'test-service', 'test-role', {'test': 'http://localhost:8080'})


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
            discoverer.start(GROUP)

            # When

        # Then
        sender.stop.assert_called_once()
        receiver.stop.assert_called_once()

    def test_stops_sender_and_receiver_when_stopped(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP)

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
        discoverer.start(GROUP)

        # Then
        sender.start.assert_called_once_with(GROUP.query())
        receiver.start.assert_called_once_with(GROUP.hello())

    def test_registers_event_handler_for_all_event_types(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        handler = MagicMock(spec=OnDiscoveryEvent)

        # When
        discoverer.register(handler)

        # Then
        self.assertIn(handler, discoverer._handlers[DiscoveryEventType.DISCOVERED])
        self.assertIn(handler, discoverer._handlers[DiscoveryEventType.UPDATED])
        self.assertIn(handler, discoverer._handlers[DiscoveryEventType.UNCHANGED])

    def test_registers_event_handler_for_single_event_type(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        handler = MagicMock(spec=OnDiscoveryEvent)

        # When
        discoverer.register(handler, {DiscoveryEventType.DISCOVERED})

        # Then
        self.assertIn(handler, discoverer._handlers[DiscoveryEventType.DISCOVERED])
        self.assertNotIn(handler, discoverer._handlers[DiscoveryEventType.UPDATED])
        self.assertNotIn(handler, discoverer._handlers[DiscoveryEventType.UNCHANGED])

    def test_deregisters_event_handler_for_all_event_types(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        handler = MagicMock(spec=OnDiscoveryEvent)
        discoverer.register(handler)

        # When
        discoverer.deregister(handler)

        # Then
        self.assertNotIn(handler, discoverer._handlers)

    def test_deregisters_event_handler_for_single_event_type(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        handler = MagicMock(spec=OnDiscoveryEvent)
        discoverer.register(handler)

        # When
        discoverer.deregister(handler, {DiscoveryEventType.UNCHANGED})

        # Then
        self.assertIn(handler, discoverer._handlers[DiscoveryEventType.DISCOVERED])
        self.assertIn(handler, discoverer._handlers[DiscoveryEventType.UPDATED])
        self.assertNotIn(handler, discoverer._handlers[DiscoveryEventType.UNCHANGED])

    def test_caches_service_and_calls_handler_when_receives_matching_service(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP, SERVICE_QUERY)
        handler = MagicMock(spec=OnDiscoveryEvent)
        discoverer.register(handler, {DiscoveryEventType.DISCOVERED})

        # When
        discoverer._handle_message(SERVICE.to_dict())

        # Then
        self.assertEqual({SERVICE.uuid: SERVICE}, discoverer.get_services())
        wait_for_assertion(1, lambda: handler.assert_called_once_with(
            DiscoveryEvent(GROUP, SERVICE_QUERY, SERVICE, DiscoveryEventType.DISCOVERED)
        ))

    def test_updates_service_and_calls_handler_when_receives_matching_service(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP, SERVICE_QUERY)
        handler = MagicMock(spec=OnDiscoveryEvent)
        discoverer.register(handler)
        discoverer._handle_message(SERVICE.to_dict())
        handler.reset_mock()
        new_service = Service(
            SERVICE.uuid, SERVICE.name, SERVICE.role, {'test': 'http://localhost:9090'}
        )

        # When
        discoverer._handle_message(new_service.to_dict())

        # Then
        self.assertEqual({SERVICE.uuid: new_service}, discoverer.get_services())
        wait_for_assertion(1, lambda: handler.assert_called_once_with(
            DiscoveryEvent(GROUP, SERVICE_QUERY, new_service, DiscoveryEventType.UPDATED)
        ))

    def test_does_not_call_handler_when_service_not_changed(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP, SERVICE_QUERY)
        handler = MagicMock(spec=OnDiscoveryEvent)
        discoverer.register(handler)
        discoverer._handle_message(SERVICE.to_dict())
        handler.reset_mock()

        # When
        discoverer._handle_message(SERVICE.to_dict())

        # Then
        handler.assert_not_called()

    def test_handles_handler_error_gracefully(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP, SERVICE_QUERY)
        handler = MagicMock(spec=OnDiscoveryEvent)
        handler.side_effect = Exception("Handler error")
        discoverer.register(handler)

        # When
        discoverer._handle_message(SERVICE.to_dict())

        # Then
        self.assertEqual({SERVICE.uuid: SERVICE}, discoverer.get_services())
        wait_for_assertion(1, lambda: handler.assert_called_once_with(
            DiscoveryEvent(GROUP, SERVICE_QUERY, SERVICE, DiscoveryEventType.DISCOVERED)
        ))

    def test_handles_invalid_message_gracefully(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP, SERVICE_QUERY)

        # When
        discoverer._handle_message({'invalid': 'message'})

        # Then
        self.assertEqual({}, discoverer.get_services())

    def test_does_not_cache_service_when_info_not_matching_query(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP, SERVICE_QUERY)

        non_matching_info = Service(uuid4(), 'other-service', 'test-role', {'test': 'http://localhost:8080'})

        # When
        discoverer._handle_message(non_matching_info.to_dict())

        # Then
        self.assertEqual({}, discoverer.get_services())

    def test_does_not_cache_service_when_no_query_set(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP)

        # When
        discoverer._handle_message(SERVICE.to_dict())

        # Then
        self.assertEqual({}, discoverer.get_services())

    def test_sends_query_when_passed_at_start(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP, SERVICE_QUERY)

        # When
        discoverer.discover()

        # Then
        sender.send.assert_called_once_with(SERVICE_QUERY)

    def test_sends_query_when_passed_at_discover(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP)

        # When
        discoverer.discover(SERVICE_QUERY)

        # Then
        sender.send.assert_called_once_with(SERVICE_QUERY)

    def test_sends_last_query_when_passed_at_start_and_at_discover(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP, ServiceQuery('other-.*', 'test-.*'))

        # When
        discoverer.discover(SERVICE_QUERY)

        # Then
        sender.send.assert_called_once_with(SERVICE_QUERY)

    def test_does_not_send_query_when_no_query_provided(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        discoverer = DefaultDiscoverer(sender, receiver)
        discoverer.start(GROUP)

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

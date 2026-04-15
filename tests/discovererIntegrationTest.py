import unittest
from unittest import TestCase
from uuid import uuid4

from common_utility import ReusableTimer
from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context

from hello import Service, Group, RadioSender, DishReceiver, ServiceQuery, DefaultDiscoverer, ScheduledDiscoverer

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_QUERY = ServiceQuery('test-service', 'test-role')
SERVICE = Service(uuid4(), 'test-service', 'test-role', {'test': 'http://localhost:8080'})


class DiscovererIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_discovers_service_when_hello_received(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)

        with DefaultDiscoverer(sender, receiver) as discoverer, RadioSender(context) as test_sender:
            test_sender.start(GROUP.hello())
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            test_sender.send(SERVICE)

            wait_for_assertion(1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE.uuid: SERVICE}, discoverer.get_services())

    def test_updates_service_when_service_changed(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)

        with DefaultDiscoverer(sender, receiver) as discoverer, RadioSender(context) as test_sender:
            test_sender.start(GROUP.hello())
            discoverer.start(GROUP, SERVICE_QUERY)

            test_sender.send(SERVICE)

            wait_for_assertion(1, lambda: self.assertEqual(1, len(discoverer.get_services())))

            # When
            new_service = Service(
                SERVICE.uuid, SERVICE.name, SERVICE.role, {'test': 'http://localhost:9090'}
            )
            test_sender.send(new_service)

            wait_for_assertion(1, lambda: self.assertEqual(
                'http://localhost:9090',
                discoverer.get_services()[SERVICE.uuid].urls['test']
            ))

        # Then
        self.assertEqual(
            'http://localhost:9090',
            discoverer.get_services()[SERVICE.uuid].urls['test']
        )

    def test_sends_query(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)
        messages = []

        with DefaultDiscoverer(sender, receiver) as discoverer, DishReceiver(context) as test_receiver:
            test_receiver.register(lambda message: messages.append(message))
            test_receiver.start(GROUP.query())
            discoverer.start(GROUP)

            # When
            discoverer.discover(SERVICE_QUERY)

            wait_for_assertion(1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([SERVICE_QUERY.__dict__], messages)

    def test_sends_query_when_schedules_discovery_once(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)
        discoverer = DefaultDiscoverer(sender, receiver)
        timer = ReusableTimer()
        messages = []

        with ScheduledDiscoverer(discoverer, timer) as scheduled_discoverer, DishReceiver(context) as test_receiver:
            test_receiver.start(GROUP.query())
            test_receiver.register(lambda message: messages.append(message))
            scheduled_discoverer.start(GROUP)

            # When
            scheduled_discoverer.schedule_one_shot(SERVICE_QUERY, interval=0.01)

            wait_for_assertion(1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([SERVICE_QUERY.__dict__], messages)

    def test_sends_query_when_schedules_discovery_periodically(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)
        discoverer = DefaultDiscoverer(sender, receiver)
        timer = ReusableTimer()
        messages = []

        with ScheduledDiscoverer(discoverer, timer) as scheduled_discoverer, DishReceiver(context) as test_receiver:
            test_receiver.start(GROUP.query())
            test_receiver.register(lambda message: messages.append(message))
            scheduled_discoverer.start(GROUP)

            # When
            scheduled_discoverer.schedule_periodic(SERVICE_QUERY, interval=0.01)

            # Then
            wait_for_assertion(1, lambda: self.assertTrue(len(messages) >= 10))


if __name__ == '__main__':
    unittest.main()

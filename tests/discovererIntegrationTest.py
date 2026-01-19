import unittest
from unittest import TestCase

from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context

from hello import ServiceInfo, Group, RadioSender, DishReceiver, GroupAccess, \
    ServiceQuery, DefaultDiscoverer

ACCESS_URL = 'udp://239.0.0.1:5555'
GROUP_NAME = 'test-group'
GROUP = Group(GROUP_NAME)
SERVICE_QUERY = ServiceQuery('test-service', 'test-role')


class DiscovererIntegrationTest(TestCase):
    SERVICE_INFO = ServiceInfo('test-service', 'test-role', 'http://localhost:8080')

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()
        self.SERVICE_INFO = ServiceInfo('test-service', 'test-role', 'http://localhost:8080')

    def test_discovers_service_when_hello_received(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)

        with DefaultDiscoverer(sender, receiver) as discoverer, RadioSender(context) as test_sender:
            test_sender.start(GroupAccess(ACCESS_URL, GROUP.hello()))
            discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)

            # When
            test_sender.send(self.SERVICE_INFO)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({self.SERVICE_INFO.name: self.SERVICE_INFO}, discoverer.get_services())

    def test_updates_service_when_info_changed(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)

        with DefaultDiscoverer(sender, receiver) as discoverer, RadioSender(context) as test_sender:
            test_sender.start(GroupAccess(ACCESS_URL, GROUP.hello()))
            discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)

            test_sender.send(self.SERVICE_INFO)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

            # When
            self.SERVICE_INFO.url = 'http://localhost:9090'
            test_sender.send(self.SERVICE_INFO)

            wait_for_assertion(0.1, lambda: self.assertEqual(
                'http://localhost:9090',
                discoverer.get_services()[self.SERVICE_INFO.name].url
            ))

        # Then
        self.assertEqual(
            'http://localhost:9090',
            discoverer.get_services()[self.SERVICE_INFO.name].url
        )

    def test_sends_query(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)
        messages = []

        with DefaultDiscoverer(sender, receiver) as discoverer, DishReceiver(context) as test_receiver:
            test_receiver.register(lambda message: messages.append(message))
            test_receiver.start(GroupAccess(ACCESS_URL, GROUP.query()))
            discoverer.start(ACCESS_URL, GROUP)

            # When
            discoverer.discover(SERVICE_QUERY)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([SERVICE_QUERY.__dict__], messages)


if __name__ == '__main__':
    unittest.main()

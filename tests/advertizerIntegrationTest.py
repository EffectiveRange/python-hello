import unittest
from unittest import TestCase

from common_utility import ReusableTimer
from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context

from hello import DefaultAdvertizer, ServiceInfo, Group, RadioSender, DishReceiver, RespondingAdvertizer, \
    ServiceQuery, ScheduledAdvertizer

GROUP = Group('test-group', 'udp://239.0.0.1:5555')


class AdvertizerIntegrationTest(TestCase):
    SERVICE_INFO = ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:8080'})

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()
        self.SERVICE_INFO = ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:8080'})

    def test_sends_hello_when_advertises_service(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        messages = []

        with DefaultAdvertizer(sender) as advertizer, DishReceiver(context) as test_receiver:
            test_receiver.start(GROUP.hello())
            test_receiver.register(lambda message: messages.append(message))
            advertizer.start(GROUP)

            # When
            advertizer.advertise(self.SERVICE_INFO)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([self.SERVICE_INFO.__dict__], messages)

    def test_sends_hello_when_query_received(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)
        messages = []

        with (RespondingAdvertizer(sender, receiver, 0.01) as advertizer,
              RadioSender(context) as test_sender,
              DishReceiver(context) as test_receiver):
            test_sender.start(GROUP.query())
            test_receiver.start(GROUP.hello())
            test_receiver.register(lambda message: messages.append(message))

            advertizer.start(GROUP, self.SERVICE_INFO)

            # When
            test_sender.send(ServiceQuery('test-service', 'test-role'))

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([self.SERVICE_INFO.__dict__], messages)

    def test_sends_hello_when_info_changed_and_query_received(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        receiver = DishReceiver(context)
        messages = []

        with (RespondingAdvertizer(sender, receiver, 0.01) as advertizer,
              RadioSender(context) as test_sender,
              DishReceiver(context) as test_receiver):
            test_sender.start(GROUP.query())
            test_receiver.start(GROUP.hello())
            test_receiver.register(lambda message: messages.append(message))

            advertizer.start(GROUP)
            advertizer.advertise(self.SERVICE_INFO)

            query = ServiceQuery('test-service', 'test-role')
            test_sender.send(query)

            wait_for_assertion(0.1, lambda: self.assertEqual(2, len(messages)))

            self.SERVICE_INFO.urls['test'] = 'http://localhost:9090'
            advertizer.advertise(self.SERVICE_INFO)

            # When
            test_sender.send(query)

            wait_for_assertion(0.1, lambda: self.assertEqual(4, len(messages)))

        # Then
        self.assertEqual([
            {'name': 'test-service', 'role': 'test-role', 'urls': {'test': 'http://localhost:8080'}},
            {'name': 'test-service', 'role': 'test-role', 'urls': {'test': 'http://localhost:8080'}},
            {'name': 'test-service', 'role': 'test-role', 'urls': {'test': 'http://localhost:9090'}},
            {'name': 'test-service', 'role': 'test-role', 'urls': {'test': 'http://localhost:9090'}}
        ], messages)

    def test_sends_hello_when_schedules_advertisement_once(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        advertizer = DefaultAdvertizer(sender)
        timer = ReusableTimer()
        messages = []

        with ScheduledAdvertizer(advertizer, timer) as scheduled_advertizer, DishReceiver(context) as test_receiver:
            test_receiver.start(GROUP.hello())
            test_receiver.register(lambda message: messages.append(message))
            scheduled_advertizer.start(GROUP)

            # When
            scheduled_advertizer.schedule(self.SERVICE_INFO, interval=0.01, one_shot=True)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([self.SERVICE_INFO.__dict__], messages)

    def test_sends_hello_when_schedules_advertisement_periodically(self):
        # Given
        context = Context()
        sender = RadioSender(context)
        advertizer = DefaultAdvertizer(sender)
        timer = ReusableTimer()
        messages = []

        with ScheduledAdvertizer(advertizer, timer) as scheduled_advertizer, DishReceiver(context) as test_receiver:
            test_receiver.start(GROUP.hello())
            test_receiver.register(lambda message: messages.append(message))
            scheduled_advertizer.start(GROUP)

            # When
            scheduled_advertizer.schedule(self.SERVICE_INFO, interval=0.01)

            # Then
            wait_for_assertion(0.1, lambda: self.assertEqual(5, len(messages)))


if __name__ == '__main__':
    unittest.main()

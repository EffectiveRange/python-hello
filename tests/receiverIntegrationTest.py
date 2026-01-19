import unittest
from unittest import TestCase

from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context

from hello import ServiceInfo, Group, DishReceiver, GroupAccess, RadioSender

ACCESS_URL = 'udp://239.0.0.1:5555'
GROUP_NAME = 'test-group'
GROUP = Group(GROUP_NAME)
SERVICE_INFO = ServiceInfo('test-service', 'test-role', 'http://localhost:8080')


class ReceiverTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_raises_error_when_restarted(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = Context()

        with DishReceiver(context) as receiver:
            receiver.start(group_access)

            # When, Then
            with self.assertRaises(RuntimeError):
                receiver.start(group_access)

    def test_receives_message(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = Context()
        messages = []

        with DishReceiver(context) as receiver, RadioSender(context) as test_sender:
            receiver.register(lambda message: messages.append(message))
            receiver.start(group_access)
            test_sender.start(group_access)

            # When
            test_sender.send(SERVICE_INFO)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([SERVICE_INFO.__dict__], messages)


if __name__ == '__main__':
    unittest.main()

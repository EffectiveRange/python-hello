import unittest
from unittest import TestCase

from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context

from hello import ServiceInfo, Group, DishReceiver
from hello.sender import RadioSender

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_INFO = ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:8080'})


class SenderIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_sends_message(self):
        # Given
        group_access = GROUP.hello()
        context = Context()
        messages = []

        with RadioSender(context) as sender, DishReceiver(context) as test_receiver:
            test_receiver.register(lambda message: messages.append(message))
            test_receiver.start(group_access)
            sender.start(group_access)

            # When
            sender.send(SERVICE_INFO)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([SERVICE_INFO.__dict__], messages)


if __name__ == '__main__':
    unittest.main()

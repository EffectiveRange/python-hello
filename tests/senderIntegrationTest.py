import unittest
from threading import Thread
from unittest import TestCase

from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context, DISH

from hello import ServiceInfo, Group
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
        group = GROUP.hello()
        context = Context()
        dish = context.socket(DISH)
        dish.bind(group.url)
        dish.join(group.name)
        messages = []

        with RadioSender(context) as sender:
            sender.start(group)
            Thread(target=lambda: messages.append(dish.recv_json())).start()

            # When
            sender.send(SERVICE_INFO)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([SERVICE_INFO.__dict__], messages)


if __name__ == '__main__':
    unittest.main()

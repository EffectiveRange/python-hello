import unittest
from unittest import TestCase

from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context, RADIO

from hello import ServiceInfo, Group, DishReceiver

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_INFO = ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:8080'})


class ReceiverIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_receives_message(self):
        # Given
        group = GROUP.hello()
        context = Context()
        radio = context.socket(RADIO)
        radio.connect(group.url)
        messages = []

        with DishReceiver(context) as receiver:
            receiver.register(lambda message: messages.append(message))
            receiver.start(group)

            # When
            radio.send_json(SERVICE_INFO.__dict__, group=group.name)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([SERVICE_INFO.__dict__], messages)


if __name__ == '__main__':
    unittest.main()

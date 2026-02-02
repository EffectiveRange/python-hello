import unittest
from unittest import TestCase
from uuid import uuid4

from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context, RADIO

from hello import ServiceInfo, Group, DishReceiver

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_INFO = ServiceInfo(uuid4(), 'test-service', 'test-role', {'test': 'http://localhost:8080'})


class ReceiverIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_receives_message(self):
        # Given
        context = Context()
        messages = []

        with DishReceiver(context) as receiver, context.socket(RADIO) as radio:
            group = GROUP.hello()
            radio.connect(group.url)
            receiver.register(lambda message: messages.append(message))
            receiver.start(group)

            # When
            radio.send_json(SERVICE_INFO.to_dict(), group=group.name)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(messages)))

        # Then
        self.assertEqual([SERVICE_INFO.to_dict()], messages)


if __name__ == '__main__':
    unittest.main()

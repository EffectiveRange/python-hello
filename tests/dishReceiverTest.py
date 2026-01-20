import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context, ZMQError, Poller, POLLIN

from hello import ServiceInfo, Group, DishReceiver, OnMessage

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_INFO = ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:8080'})


class DishReceiverTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_raises_error_when_restarted(self):
        # Given
        group_access = GROUP.hello()
        context = MagicMock(spec=Context)

        with DishReceiver(context) as receiver:
            receiver.start(group_access)

            # When, Then
            with self.assertRaises(RuntimeError):
                receiver.start(group_access)

    def test_raises_error_when_fails_to_bind_socket(self):
        # Given
        group_access = GROUP.hello()
        context = MagicMock(spec=Context)
        context.socket.return_value.bind.side_effect = ZMQError(1, "Bind failed")
        receiver = DishReceiver(context)

        # When, Then
        with self.assertRaises(ZMQError):
            receiver.start(group_access)

    def test_closes_socket_on_exit(self):
        # Given
        group_access = GROUP.hello()
        context = MagicMock(spec=Context)

        with DishReceiver(context) as receiver:
            receiver.start(group_access)

            # When

        # Then
        context.socket.return_value.close.assert_called_once()

    def test_closes_socket_when_stopped(self):
        # Given
        group_access = GROUP.hello()
        context = MagicMock(spec=Context)
        receiver = DishReceiver(context)
        receiver.start(group_access)

        # When
        receiver.stop()

        # Then
        context.socket.return_value.close.assert_called_once()

    def test_raises_error_when_fails_to_close_socket_on_stop(self):
        # Given
        group_access = GROUP.hello()
        context = MagicMock(spec=Context)
        context.socket.return_value.close.side_effect = [ZMQError(1, "Close failed"), None]

        with DishReceiver(context) as receiver:
            receiver.start(group_access)

            # When, Then
            with self.assertRaises(ZMQError):
                receiver.stop()

    def test_registers_handler(self):
        # Given
        context = MagicMock(spec=Context)
        receiver = DishReceiver(context)
        handler = MagicMock(spec=OnMessage)

        # When
        receiver.register(handler)

        # Then
        self.assertIn(handler, receiver.get_handlers())

    def test_deregisters_handler(self):
        # Given
        context = MagicMock(spec=Context)
        receiver = DishReceiver(context)
        handler = MagicMock(spec=OnMessage)
        receiver.register(handler)

        # When
        receiver.deregister(handler)

        # Then
        self.assertNotIn(handler, receiver.get_handlers())

    def test_calls_registered_handler_on_message(self):
        # Given
        group_access = GROUP.hello()
        context = MagicMock(spec=Context)
        context.socket.return_value.recv_json.return_value = SERVICE_INFO.__dict__
        handler = MagicMock(spec=OnMessage)

        with DishReceiver(context) as receiver:
            receiver._poller = MagicMock(spec=Poller)
            receiver._poller.poll.side_effect = [
                {context.socket.return_value: POLLIN},
            ]
            receiver.register(handler)

            # When
            receiver.start(group_access)

            # Then
            wait_for_assertion(0.1, lambda: handler.assert_called_once_with(SERVICE_INFO.__dict__))

    def test_handles_message_receive_error_gracefully(self):
        # Given
        group_access = GROUP.hello()
        context = MagicMock(spec=Context)
        context.socket.return_value.recv_json.side_effect = ZMQError(1, "Receive failed")
        handler = MagicMock(spec=OnMessage)

        with DishReceiver(context) as receiver:
            receiver._poller = MagicMock(spec=Poller)
            receiver._poller.poll.side_effect = [
                {context.socket.return_value: POLLIN},
            ]
            receiver.register(handler)

            # When
            receiver.start(group_access)

            # Then
            handler.assert_not_called()

    def test_handles_handler_execution_error_gracefully(self):
        # Given
        group_access = GROUP.hello()
        context = MagicMock(spec=Context)
        context.socket.return_value.recv_json.return_value = SERVICE_INFO.__dict__
        handler = MagicMock(spec=OnMessage)
        handler.side_effect = Exception("Execution failed")

        with DishReceiver(context) as receiver:
            receiver._poller = MagicMock(spec=Poller)
            receiver._poller.poll.side_effect = [
                {context.socket.return_value: POLLIN},
            ]
            receiver.register(handler)

            # When
            receiver.start(group_access)

            # Then
            wait_for_assertion(0.1, lambda: handler.assert_called_once_with(SERVICE_INFO.__dict__))


if __name__ == '__main__':
    unittest.main()

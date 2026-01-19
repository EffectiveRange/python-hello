import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging
from zmq import Context, ZMQError

from hello import ServiceInfo, Group, GroupAccess
from hello.sender import RadioSender

ACCESS_URL = 'udp://239.0.0.1:5555'
GROUP_NAME = 'test-group'
GROUP = Group(GROUP_NAME)
SERVICE_INFO = ServiceInfo('test-service', 'test-role', 'http://localhost:8080')


class RadioSenderTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_raises_error_when_restarted(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = MagicMock(spec=Context)
        sender = RadioSender(context)
        sender.start(group_access)

        # When, Then
        with self.assertRaises(RuntimeError):
            sender.start(group_access)

    def test_raises_error_when_fails_to_connect_socket(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = MagicMock(spec=Context)
        context.socket.return_value.connect.side_effect = ZMQError(1, "Connect failed")
        sender = RadioSender(context)

        # When, Then
        with self.assertRaises(ZMQError):
            sender.start(group_access)

    def test_closes_socket_on_exit(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = MagicMock(spec=Context)

        with RadioSender(context) as sender:
            sender.start(group_access)

            # When

        # Then
        context.socket.return_value.close.assert_called_once()

    def test_closes_socket_when_stopped(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = MagicMock(spec=Context)
        sender = RadioSender(context)
        sender.start(group_access)

        # When
        sender.stop()

        # Then
        context.socket.return_value.close.assert_called_once()

    def test_raises_error_when_fails_to_close_socket_on_stop(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = MagicMock(spec=Context)
        context.socket.return_value.close.side_effect = ZMQError(1, "Close failed")
        sender = RadioSender(context)
        sender.start(group_access)

        # When, Then
        with self.assertRaises(ZMQError):
            sender.stop()

    def test_sends_message_when_convertible_to_dict(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = MagicMock(spec=Context)
        sender = RadioSender(context)
        sender.start(group_access)

        # When
        sender.send(SERVICE_INFO)

        # Then
        context.socket.return_value.send_json.assert_called_with(SERVICE_INFO.__dict__, group='hello:test-group')

    def test_sends_message_when_type_is_dict(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = MagicMock(spec=Context)
        sender = RadioSender(context)
        sender.start(group_access)

        # When
        sender.send(SERVICE_INFO.__dict__)

        # Then
        context.socket.return_value.send_json.assert_called_with(SERVICE_INFO.__dict__, group='hello:test-group')

    def test_does_not_send_message_when_not_serializable(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = MagicMock(spec=Context)
        sender = RadioSender(context)
        sender.start(group_access)

        # When
        sender.send("not serializable message")

        # Then
        context.socket.return_value.send_json.assert_not_called()

    def test_does_not_send_message_when_not_started(self):
        # Given
        context = MagicMock(spec=Context)
        sender = RadioSender(context)

        # When
        sender.send(SERVICE_INFO)

        # Then
        context.socket.return_value.send_json.assert_not_called()

    def test_handles_send_message_error_gracefully(self):
        # Given
        group_access = GroupAccess(ACCESS_URL, GROUP.hello())
        context = MagicMock(spec=Context)
        sender = RadioSender(context)
        sender.start(group_access)
        context.socket.return_value.send_json.side_effect = ZMQError(1, "Send failed")

        # When
        sender.send(SERVICE_INFO)

        # Then
        context.socket.return_value.send_json.assert_called_once_with(SERVICE_INFO.__dict__, group='hello:test-group')


if __name__ == '__main__':
    unittest.main()

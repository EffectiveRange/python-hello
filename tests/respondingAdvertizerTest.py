import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging

from hello import ServiceInfo, Group, Sender, GroupAccess, Receiver, RespondingAdvertizer, ServiceQuery

ACCESS_URL = 'udp://239.0.0.1:5555'
GROUP_NAME = 'test-group'
GROUP = Group(GROUP_NAME)
SERVICE_INFO = ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:8080'})


class RespondingAdvertizerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_stops_sender_and_receiver_on_exit(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)

        with RespondingAdvertizer(sender, receiver) as advertizer:
            advertizer.start(ACCESS_URL, GROUP)

            # When

        # Then
        sender.stop.assert_called_once()
        receiver.stop.assert_called_once()

    def test_stops_sender_and_receiver_when_stopped(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        advertizer = RespondingAdvertizer(sender, receiver)
        advertizer.start(ACCESS_URL, GROUP)

        # When
        advertizer.stop()

        # Then
        sender.stop.assert_called_once()
        receiver.stop.assert_called_once()

    def test_starts_sender_and_receiver_when_started(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        advertizer = RespondingAdvertizer(sender, receiver)

        # When
        advertizer.start(ACCESS_URL, GROUP)

        # Then
        sender.start.assert_called_once_with(GroupAccess(ACCESS_URL, GROUP.hello()))
        receiver.start.assert_called_once_with(GroupAccess(ACCESS_URL, GROUP.query()))

    def test_sends_service_info_when_receives_matching_query(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        advertizer = RespondingAdvertizer(sender, receiver)
        advertizer.start(ACCESS_URL, GROUP, SERVICE_INFO)

        # When
        advertizer._handle_message(ServiceQuery('test-.*', 'test-.*').__dict__)

        # Then
        sender.send.assert_called_once_with(SERVICE_INFO)

    def test_does_not_send_service_info_when_receives_non_matching_query(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        advertizer = RespondingAdvertizer(sender, receiver)
        advertizer.start(ACCESS_URL, GROUP, SERVICE_INFO)

        # When
        advertizer._handle_message(ServiceQuery('other-.*', 'test-.*').__dict__)

        # Then
        sender.send.assert_not_called()

    def test_does_not_send_service_info_when_no_service_info_set(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        advertizer = RespondingAdvertizer(sender, receiver)
        advertizer.start(ACCESS_URL, GROUP)

        # When
        advertizer._handle_message(ServiceQuery('test-.*', 'test-.*').__dict__)

        # Then
        sender.send.assert_not_called()

    def test_handles_invalid_message_gracefully(self):
        # Given
        sender = MagicMock(spec=Sender)
        receiver = MagicMock(spec=Receiver)
        advertizer = RespondingAdvertizer(sender, receiver)
        advertizer.start(ACCESS_URL, GROUP, SERVICE_INFO)

        # When
        advertizer._handle_message({'invalid': 'message'})

        # Then
        sender.send.assert_not_called()


if __name__ == '__main__':
    unittest.main()

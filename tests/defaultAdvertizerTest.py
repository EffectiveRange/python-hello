import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging

from hello import ServiceInfo, Group, Sender, DefaultAdvertizer

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_INFO = ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:8080'})


class DefaultAdvertizerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_stops_sender_on_exit(self):
        # Given
        sender = MagicMock(spec=Sender)

        with DefaultAdvertizer(sender) as advertizer:
            advertizer.start(GROUP)

            # When

        # Then
        sender.stop.assert_called_once()

    def test_stops_sender_when_stopped(self):
        # Given
        sender = MagicMock(spec=Sender)
        advertizer = DefaultAdvertizer(sender)
        advertizer.start(GROUP)

        # When
        advertizer.stop()

        # Then
        sender.stop.assert_called_once()

    def test_starts_sender_when_started(self):
        # Given
        sender = MagicMock(spec=Sender)
        advertizer = DefaultAdvertizer(sender)

        # When
        advertizer.start(GROUP)

        # Then
        sender.start.assert_called_once_with(GROUP.hello())

    def test_sends_info_when_passed_at_start(self):
        # Given
        sender = MagicMock(spec=Sender)
        advertizer = DefaultAdvertizer(sender)
        advertizer.start(GROUP, SERVICE_INFO)

        # When
        advertizer.advertise()

        # Then
        sender.send.assert_called_once_with(SERVICE_INFO)

    def test_sends_info_when_passed_at_advertise(self):
        # Given
        sender = MagicMock(spec=Sender)
        advertizer = DefaultAdvertizer(sender)
        advertizer.start(GROUP)

        # When
        advertizer.advertise(SERVICE_INFO)

        # Then
        sender.send.assert_called_once_with(SERVICE_INFO)

    def test_sends_last_info_when_passed_at_start_and_at_advertise(self):
        # Given
        sender = MagicMock(spec=Sender)
        advertizer = DefaultAdvertizer(sender)
        advertizer.start(GROUP, ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:9090'}))

        # When
        advertizer.advertise(SERVICE_INFO)

        # Then
        sender.send.assert_called_once_with(SERVICE_INFO)

    def test_does_not_send_info_when_no_info_provided(self):
        # Given
        sender = MagicMock(spec=Sender)
        advertizer = DefaultAdvertizer(sender)
        advertizer.start(GROUP)

        # When
        advertizer.advertise()

        # Then
        sender.send.assert_not_called()

    def test_does_not_send_info_when_not_started(self):
        # Given
        sender = MagicMock(spec=Sender)
        advertizer = DefaultAdvertizer(sender)

        # When
        advertizer.advertise(SERVICE_INFO)

        # Then
        sender.send.assert_not_called()


if __name__ == '__main__':
    unittest.main()

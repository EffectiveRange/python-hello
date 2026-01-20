import unittest
from unittest import TestCase

from context_logger import setup_logging
from test_utility import wait_for_assertion

from hello import ServiceInfo, Group, ServiceQuery, Hello, HelloConfig

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_INFO = ServiceInfo('test-service', 'test-role', {'test': 'http://localhost:8080'})
SERVICE_QUERY = ServiceQuery('test-service', 'test-role')


class ApiIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_discoverer_caches_advertised_service(self):
        # Given
        config = HelloConfig(advertizer_responder=False)

        with Hello.default_advertizer(config) as advertizer, Hello.default_discoverer(config) as discoverer:
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            advertizer.advertise()

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.name: SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_advertised_service_when_scheduled_once(self):
        # Given
        config = HelloConfig(advertizer_responder=False)

        with Hello.scheduled_advertizer(config) as advertizer, Hello.default_discoverer(config) as discoverer:
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            advertizer.schedule(interval=0.01, one_shot=True)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.name: SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_advertised_service_when_scheduled_periodically(self):
        # Given
        config = HelloConfig()

        with Hello.scheduled_advertizer(config) as advertizer, Hello.default_discoverer(config) as discoverer:
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            advertizer.schedule(interval=0.01)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.name: SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_discovery_response_service(self):
        # Given
        config = HelloConfig()

        with Hello.default_advertizer(config) as advertizer, Hello.default_discoverer(config) as discoverer:
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            discoverer.discover()

            wait_for_assertion(0.2, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.name: SERVICE_INFO}, discoverer.get_services())


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest import TestCase

from context_logger import setup_logging
from test_utility import wait_for_assertion
from zmq import Context

from hello import ServiceInfo, Group, DefaultHello, ServiceQuery

ACCESS_URL = 'udp://239.0.0.1:5555'
GROUP_NAME = 'test-group'
GROUP = Group(GROUP_NAME)
SERVICE_INFO = ServiceInfo('test-service', 'test-role', 'http://localhost:8080')
SERVICE_QUERY = ServiceQuery('test-service', 'test-role')


class ApiTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()
        self.SERVICE_INFO = ServiceInfo('test-service', 'test-role', 'http://localhost:8080')

    def test_discoverer_caches_advertised_service(self):
        # Given
        context = Context()
        hello = DefaultHello(context)

        with hello.default_advertizer() as advertizer, hello.discoverer() as discoverer:
            advertizer.start(ACCESS_URL, GROUP, SERVICE_INFO)
            discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)

            # When
            advertizer.advertise()

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({self.SERVICE_INFO.name: self.SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_advertised_service_when_scheduled_once(self):
        # Given
        context = Context()
        hello = DefaultHello(context)

        with hello.scheduled_advertizer() as advertizer, hello.discoverer() as discoverer:
            advertizer.start(ACCESS_URL, GROUP, SERVICE_INFO)
            discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)

            # When
            advertizer.schedule(interval=0.01, one_shot=True)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({self.SERVICE_INFO.name: self.SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_advertised_service_when_scheduled_periodically(self):
        # Given
        context = Context()
        hello = DefaultHello(context)

        with hello.scheduled_advertizer() as advertizer, hello.discoverer() as discoverer:
            advertizer.start(ACCESS_URL, GROUP, SERVICE_INFO)
            discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)

            # When
            advertizer.schedule(interval=0.01)

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({self.SERVICE_INFO.name: self.SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_discovery_response_service(self):
        # Given
        context = Context()
        hello = DefaultHello(context)

        with hello.default_advertizer() as advertizer, hello.discoverer() as discoverer:
            advertizer.start(ACCESS_URL, GROUP, SERVICE_INFO)
            discoverer.start(ACCESS_URL, GROUP, SERVICE_QUERY)

            # When
            discoverer.discover()

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({self.SERVICE_INFO.name: self.SERVICE_INFO}, discoverer.get_services())


if __name__ == '__main__':
    unittest.main()

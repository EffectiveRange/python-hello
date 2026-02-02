import unittest
from threading import Thread
from unittest import TestCase
from uuid import uuid4

from context_logger import setup_logging
from test_utility import wait_for_assertion

from hello import ServiceInfo, Group, ServiceQuery, Hello, HelloConfig

GROUP = Group('test-group', 'udp://239.0.0.1:5555')
SERVICE_INFO = ServiceInfo(uuid4(), 'test-service', 'test-role', {'test': 'http://localhost:8080'})
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

        with (Hello.builder(config).advertizer().default() as advertizer,
              Hello.builder(config).discoverer().default() as discoverer):
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            advertizer.advertise()

            wait_for_assertion(0.1, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.uuid: SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_advertised_services(self):
        # Given
        config = HelloConfig(advertizer_responder=False)

        with (Hello.builder(config).advertizer().default() as advertizer1,
              Hello.builder(config).advertizer().default() as advertizer2,
              Hello.builder(config).discoverer().default() as discoverer):
            service_info1 = ServiceInfo(uuid4(), 'test-service1', 'test-role', {'test': 'http://localhost:8080'})
            service_info2 = ServiceInfo(uuid4(), 'test-service2', 'test-role', {'test': 'http://localhost:8080'})
            advertizer1.start(GROUP, service_info1)
            advertizer2.start(GROUP, service_info2)
            discoverer.start(GROUP, ServiceQuery('test-service.+', 'test-role'))

            # When
            for _ in range(5):
                Thread(target=advertizer1.advertise).start()
                Thread(target=advertizer2.advertise).start()

            wait_for_assertion(0.2, lambda: self.assertEqual(2, len(discoverer.get_services())))

            # Then
            self.assertEqual({
                service_info1.uuid: service_info1,
                service_info2.uuid: service_info2
            }, discoverer.get_services())

    def test_discoverer_caches_advertised_service_when_advertisement_scheduled_once(self):
        # Given
        config = HelloConfig(advertizer_responder=False)

        with (Hello.builder(config).advertizer().scheduled() as advertizer,
              Hello.builder(config).discoverer().default() as discoverer):
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            advertizer.schedule(interval=0.01, one_shot=True)

            wait_for_assertion(0.2, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.uuid: SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_advertised_service_when_advertisement_scheduled_periodically(self):
        # Given
        config = HelloConfig()

        with (Hello.builder(config).advertizer().scheduled() as advertizer,
              Hello.builder(config).discoverer().default() as discoverer):
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            advertizer.schedule(interval=0.01)

            wait_for_assertion(0.2, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.uuid: SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_discovery_response_service(self):
        # Given
        config = HelloConfig()

        with (Hello.builder(config).advertizer().default() as advertizer,
              Hello.builder(config).discoverer().default() as discoverer):
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            discoverer.discover()

            wait_for_assertion(0.2, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.uuid: SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_discovery_response_services(self):
        # Given
        config = HelloConfig()

        with (Hello.builder(config).advertizer().default() as advertizer1,
              Hello.builder(config).advertizer().default() as advertizer2,
              Hello.builder(config).discoverer().default() as discoverer):
            service_info1 = ServiceInfo(uuid4(), 'test-service1', 'test-role', {'test': 'http://localhost:8080'})
            service_info2 = ServiceInfo(uuid4(), 'test-service2', 'test-role', {'test': 'http://localhost:8080'})
            advertizer1.start(GROUP, service_info1)
            advertizer2.start(GROUP, service_info2)
            discoverer.start(GROUP, ServiceQuery('test-service.+', 'test-role'))

            # When
            discoverer.discover()

            wait_for_assertion(0.2, lambda: self.assertEqual(2, len(discoverer.get_services())))

        # Then
        self.assertEqual({
            service_info1.uuid: service_info1,
            service_info2.uuid: service_info2
        }, discoverer.get_services())

    def test_discoverer_caches_discovery_response_service_when_discovery_scheduled_once(self):
        # Given
        config = HelloConfig()

        with (Hello.builder(config).advertizer().default() as advertizer,
              Hello.builder(config).discoverer().scheduled() as discoverer):
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            discoverer.schedule(interval=0.01, one_shot=True)

            wait_for_assertion(0.2, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.uuid: SERVICE_INFO}, discoverer.get_services())

    def test_discoverer_caches_discovery_response_service_when_discovery_scheduled_periodically(self):
        # Given
        config = HelloConfig()

        with (Hello.builder(config).advertizer().default() as advertizer,
              Hello.builder(config).discoverer().scheduled() as discoverer):
            advertizer.start(GROUP, SERVICE_INFO)
            discoverer.start(GROUP, SERVICE_QUERY)

            # When
            discoverer.schedule(interval=0.01)

            wait_for_assertion(0.2, lambda: self.assertEqual(1, len(discoverer.get_services())))

        # Then
        self.assertEqual({SERVICE_INFO.uuid: SERVICE_INFO}, discoverer.get_services())


if __name__ == '__main__':
    unittest.main()

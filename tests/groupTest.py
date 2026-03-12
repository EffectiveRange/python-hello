import unittest
from unittest import TestCase

from context_logger import setup_logging

from hello import Group


class GroupTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_group_created(self):
        # When
        group = Group.create(name='test-group', address='239.0.1.1', port=5555)

        # Then
        self.assertEqual(Group(name='test-group', url='udp://239.0.1.1:5555'), group)

    def test_group_created_when_interface_address_is_provided(self):
        # When
        group = Group.create(name='test-group', address='239.0.1.1', port=5555, if_address='192.168.0.100')

        # Then
        self.assertEqual(Group(name='test-group', url='udp://192.168.0.100;239.0.1.1:5555'), group)

    def test_prefixed_group_created_with_hello_prefix(self):
        # Given
        group = Group('test-group', 'udp://239.0.1.1:5555')

        # When
        prefixed_group = group.hello()

        # Then
        self.assertEqual('hello:test-group', prefixed_group.name)
        self.assertEqual(group.url, prefixed_group.url)

    def test_prefixed_group_created_with_query_prefix(self):
        # Given
        group = Group('test-group', 'udp://239.0.1.1:5555')

        # When
        prefixed_group = group.query()

        # Then
        self.assertEqual('query:test-group', prefixed_group.name)
        self.assertEqual(group.url, prefixed_group.url)


if __name__ == '__main__':
    unittest.main()

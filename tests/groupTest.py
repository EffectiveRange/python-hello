import unittest
from unittest import TestCase

from context_logger import setup_logging

from hello import GroupUrl, Group


class GroupTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('hello', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_url_resolves_when_interface_is_not_provided(self):
        # Given
        group_url = GroupUrl(protocol='udp', address='239.0.1.1', port=5555)

        # When
        url = group_url.resolve()

        # Then
        self.assertEqual('udp://239.0.1.1:5555', url)

    def test_url_resolves_when_interface_is_provided(self):
        # Given
        group_url = GroupUrl(protocol='udp', address='239.0.1.1', port=5555, interface='lo')

        # When
        url = group_url.resolve()

        # Then
        self.assertEqual('udp://127.0.0.1;239.0.1.1:5555', url)

    def test_url_resolves_when_interface_is_provided_but_not_exists(self):
        # Given
        group_url = GroupUrl(protocol='udp', address='239.0.1.1', port=5555, interface='nonexistent0')

        # When
        url = group_url.resolve()

        # Then
        self.assertEqual('udp://239.0.1.1:5555', url)

    def test_group_created_with_resolved_url(self):
        # Given
        group_url = GroupUrl(address='239.0.1.1', port=5555, interface='lo')

        # When
        group = Group.create('test-group', group_url)

        # Then
        self.assertEqual(Group(name='test-group', url='udp://127.0.0.1;239.0.1.1:5555'), group)

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

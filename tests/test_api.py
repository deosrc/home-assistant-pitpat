import unittest
from custom_components.pitpat.api import PitPatApiClient


class ApiHostUnitTests(unittest.TestCase):

    def test_hosts_are_production(self):
        """Guard against debug/local API addresses being committed."""
        expected = {
            'AUTH': 'https://auth.pitpat.com',
            'API': 'https://api.pitpat.com',
            'ACTIVITY': 'https://activity.pitpat.com',
            'LOCATION': 'https://location.pitpat.com',
        }
        for name, url in expected.items():
            with self.subTest(name):
                self.assertEqual(url, getattr(PitPatApiClient, f'_PitPatApiClient__HOST_{name}'))

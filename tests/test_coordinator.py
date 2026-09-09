import unittest
from datetime import datetime, timedelta, timezone

from homeassistant.util import dt as dt_util

import custom_components.pitpat.coordinator as coordinator

NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)


class DayIsTodayUnitTests(unittest.TestCase):

    def test_day_is_today(self):
        inputs = [
            (None, False),
            ('', False),
            ('2026-13-99', False),
            ('2026-09-08', False),
            ('2026-09-08T23:59:59Z', False),
            ('2026-09-10', False),
            ('2026-09-09', True),
            ('2026-09-09T00:00:00Z', True),
            ('2026-09-09T23:00:00Z', True),
        ]

        for raw_input, expected in inputs:
            with self.subTest(raw_input):
                result = coordinator._day_is_today(raw_input, NOW)
                self.assertEqual(expected, result)

    def test_day_is_today_without_reference(self):
        today = dt_util.now().date()

        self.assertTrue(coordinator._day_is_today(today.isoformat()))
        self.assertFalse(coordinator._day_is_today((today - timedelta(days=1)).isoformat()))


class GetActivityTodayUnitTests(unittest.TestCase):

    def test_no_data(self):
        inputs = [None, []]

        for raw_input in inputs:
            with self.subTest(raw_input):
                self.assertIsNone(coordinator._get_activity_today(raw_input, NOW))

    def test_no_today(self):
        days = [
            {'Date': '2026-09-08', 'TotalSteps': 100},
            {'Date': '2026-09-07', 'TotalSteps': 200},
        ]

        self.assertIsNone(coordinator._get_activity_today(days, NOW))

    def test_today(self):
        days = [
            {'Date': '2026-09-08', 'TotalSteps': 100},
            {'Date': '2026-09-09', 'TotalSteps': 200},
        ]

        result = coordinator._get_activity_today(days, NOW)
        self.assertEqual(200, result.get('TotalSteps'))

    def test_most_recent_picked(self):
        days = [
            {'Date': '2026-09-07', 'TotalSteps': 100},
            {'Date': '2026-09-09', 'TotalSteps': 200},
        ]

        result = coordinator._get_activity_today(days, NOW)
        self.assertEqual(200, result.get('TotalSteps'))

    def test_invalid_dates(self):
        days = [
            {'Date': 'not-a-date', 'TotalSteps': 100},
            {'Date': None, 'TotalSteps': 100},
        ]

        self.assertIsNone(coordinator._get_activity_today(days, NOW))


if __name__ == '__main__':
    unittest.main()
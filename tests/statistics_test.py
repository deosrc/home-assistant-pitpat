import unittest
import custom_components.pitpat.statistics as statistics
import datetime

class StatisticsUnitTests(unittest.TestCase):

    def test_slug(self):
        inputs = [
            ('Scooby Doo', 'scooby_doo'),
            ('Scrappy-Doo', 'scrappy_doo'),
            ('abc!"£ 123', 'abc_123'),
        ]

        for raw_input, expected in inputs:
            with self.subTest(raw_input):
                result = statistics._slug(raw_input)
                self.assertEqual(expected, result)

    def test_day_start(self):
        inputs = [
            (None, None),
            ('2026-08-31', datetime.datetime(2026, 8, 31, tzinfo=datetime.UTC)),
            ('2026-08-31T00:00:00Z', datetime.datetime(2026, 8, 31, tzinfo=datetime.UTC)),
            ('2026-31-08T00:00:00Z', None),
            ('2026-12-31T00:00:00Z', datetime.datetime(2026, 12, 31, tzinfo=datetime.UTC)),
        ]

        for raw_input, expected in inputs:
            with self.subTest(raw_input):
                result = statistics._day_start(raw_input)
                self.assertEqual(expected, result)

    def test_get_statistic_points(self):
        # Arrange
        description = statistics.PitPatStatisticsDescription(
            statistic_key='test',
            data_key='Value',
            label='Test',
            unit_of_measurement='count',
            value_scale=0.1
        )

        inputs = [
            ('No data', [], []),
            (
                'Missing key',
                [{'Date': '2026-08-30', 'Value': 1234}, {'Date': '2026-08-31'}],
                [{'max': 123.4, 'mean': 123.4, 'min': 123.4, 'start': datetime.datetime(2026, 8, 30, tzinfo=datetime.UTC)}]
            ),
            (
                'Success',
                [{'Date': '2026-08-30', 'Value': 1234}, {'Date': '2026-08-31', 'Value': 123}],
                [
                    {'max': 123.4, 'mean': 123.4, 'min': 123.4, 'start': datetime.datetime(2026, 8, 30, tzinfo=datetime.UTC)},
                    {'max': 12.3, 'mean': 12.3, 'min': 12.3, 'start': datetime.datetime(2026, 8, 31, tzinfo=datetime.UTC)},
                ]
            ),
        ]

        for test, raw_input, expected in inputs:
            with self.subTest(test):
                # Act
                result = statistics._get_statistic_points(description, raw_input)

                # Assert
                self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

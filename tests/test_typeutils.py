import unittest
import datetime

from custom_components.pitpat.typeutils import to_nullable_datetime, to_nullable_float, to_nullable_int

class TypeUtilsUnitTests(unittest.TestCase):

    def test_to_nullable_int(self):
        inputs = [
            (None, None),
            ('', None),
            ('0', 0),
            ('5', 5),
            ('-3', -3),
        ]

        for raw_input, expected in inputs:
            with self.subTest(raw_input):
                self.assertEqual(expected, to_nullable_int(raw_input))

    def test_to_nullable_int_invalid(self):
        for raw_input in ['abc', '5.5', '1 2']:
            with self.subTest(raw_input):
                with self.assertRaises(ValueError):
                    to_nullable_int(raw_input)

    def test_to_nullable_float(self):
        inputs = [
            (None, None),
            ('', None),
            ('0', 0.0),
            ('5', 5.0),
            ('5.5', 5.5),
            ('-1.25', -1.25),
        ]

        for raw_input, expected in inputs:
            with self.subTest(raw_input):
                self.assertEqual(expected, to_nullable_float(raw_input))

    def test_to_nullable_float_invalid(self):
        for raw_input in ['abc', '1,5']:
            with self.subTest(raw_input):
                with self.assertRaises(ValueError):
                    to_nullable_float(raw_input)

    def test_to_nullable_datetime(self):
        inputs = [
            (None, None),
            ('', None),
            ('2026-08-31T00:00:00Z', datetime.datetime(2026, 8, 31, tzinfo=datetime.UTC)),
            ('2026-08-31T23:30:00Z', datetime.datetime(2026, 8, 31, 23, 30, tzinfo=datetime.UTC)),
            ('2026-08-31', datetime.datetime(2026, 8, 31)),
        ]

        for raw_input, expected in inputs:
            with self.subTest(raw_input):
                result = to_nullable_datetime(raw_input)
                self.assertEqual(expected, result)
                if expected is None:
                    self.assertIsNone(result)

    def test_to_nullable_datetime_invalid(self):
        for raw_input in ['not-a-date', '99/99/99']:
            with self.subTest(raw_input):
                with self.assertRaises(ValueError):
                    to_nullable_datetime(raw_input)

if __name__ == '__main__':
    unittest.main()
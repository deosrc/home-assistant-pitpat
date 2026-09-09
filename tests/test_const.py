import unittest
from custom_components.pitpat.const import Device

class DeviceUnitTests(unittest.TestCase):

    def test_from_model_known(self):
        inputs = [
            (3, Device.BluetoothActivityMonitor),
            (6, Device.GpsTrackerV2),
        ]

        for raw_input, expected in inputs:
            with self.subTest(raw_input):
                self.assertEqual(expected, Device.from_model(raw_input))

    def test_from_model_unknown(self):
        inputs = [None, 0, 99, '6']

        for raw_input in inputs:
            with self.subTest(raw_input):
                self.assertEqual(Device.Unknown, Device.from_model(raw_input))

if __name__ == '__main__':
    unittest.main()
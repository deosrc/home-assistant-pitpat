from enum import Enum
from typing import Dict


DOMAIN = "pitpat"
MANUFACTURER = "PitPat"

OPTIONS_KEY_UPDATE_INTERVAL = "update_interval"

DATA_KEY_COORDINATOR = "coordinator"

UPDATE_INTERVAL_DEFAULT = 5

class Device(Enum):
    Unknown = None
    BluetoothActivityMonitor = 3
    GpsTracker = 6

DEVICE_MODEL_MAP: Dict[int, str] = {
    Device.BluetoothActivityMonitor.value: 'Bluetooth Activity Monitor',
    Device.GpsTracker.value: 'GPS Tracker',
}

PHONE_HOME_CADENCE_MAP: Dict[int, str] = {
    1: 'Economy',
    0: 'Standard',
    2: 'Urgent',
}

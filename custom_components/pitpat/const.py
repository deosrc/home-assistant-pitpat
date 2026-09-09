from enum import Enum
from typing import Dict


DOMAIN = "pitpat"
MANUFACTURER = "PitPat"

OPTIONS_KEY_UPDATE_INTERVAL = "update_interval"
OPTIONS_KEY_SIGNAL_GRACE_PERIOD = "signal_grace_period"

DATA_KEY_COORDINATOR = "coordinator"

UPDATE_INTERVAL_DEFAULT = 5
SIGNAL_GRACE_PERIOD_DEFAULT = 30

class Device(Enum):
    Unknown = None
    BluetoothActivityMonitor = 3
    GpsTracker = 6

    @classmethod
    def from_model(cls, model: int | None) -> Device:
        try:
            return cls(model)
        except ValueError:
            return cls.Unknown

DEVICE_MODEL_MAP: Dict[int, str] = {
    Device.BluetoothActivityMonitor.value: 'Bluetooth Activity Monitor',
    Device.GpsTracker.value: 'GPS Tracker',
}

PHONE_HOME_CADENCE_MAP: Dict[int, str] = {
    1: 'Economy',
    0: 'Standard',
    2: 'Urgent',
}

from __future__ import annotations

from enum import Enum
from typing import Dict


DOMAIN = "pitpat"
MANUFACTURER = "PitPat"

OPTIONS_KEY_UPDATE_INTERVAL = "update_interval"
OPTIONS_KEY_SIGNAL_GRACE_PERIOD = "signal_grace_period"

DATA_KEY_COORDINATOR = "coordinator"

UPDATE_INTERVAL_DEFAULT = 5
SIGNAL_GRACE_PERIOD_DEFAULT = 30

# Device enum member names are based on current knowledge and may require
# renaming as new hardware revisions are discovered.
class Device(Enum):
    Unknown = None
    BluetoothActivityMonitor = 3
    GpsTrackerV1 = 4
    GpsTrackerV2 = 6

    @classmethod
    def from_model(cls, model: int | None) -> Device:
        try:
            return cls(model)
        except ValueError:
            return cls.Unknown

DEVICE_MODEL_MAP: Dict[int, str] = {
    Device.BluetoothActivityMonitor.value: 'Bluetooth Activity Monitor',
    Device.GpsTrackerV1.value: 'GPS Tracker',
    Device.GpsTrackerV2.value: 'GPS Tracker',
}

PHONE_HOME_CADENCE_MAP: Dict[int, str] = {
    1: 'Economy',
    0: 'Standard',
    2: 'Urgent',
}

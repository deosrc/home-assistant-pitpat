from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Any, Dict, List

import dateutil


_LOGGER = logging.getLogger(__name__)

class TrackingStatus(Enum):
    NOT_TRACKING = 0
    WAITING_FOR_CONNECTION = 1
    LISTENING_FOR_SATELLITES = 2
    TRACKING = 3

@dataclass(frozen=True, kw_only=True)
class PitPatDeviceDetails():
    model_id: int | None
    firmware_version: str | None
    hardware_version: str | None
    serial_number: str | None

@dataclass(frozen=True, kw_only=True)
class Location():
    updated: datetime
    latitude: float
    longitude: float
    accuracy: float

@dataclass(frozen=True, kw_only=True)
class PitPatTracking():
    tracking_status: TrackingStatus | None
    last_position: Location | None

@dataclass(frozen=True, kw_only=True)
class PitPatDogData():
    raw_dog_data: Dict[str, Any]
    raw_monitor_data: Dict[str, Any]
    latest_raw_activity: Dict[str, Any] | None

    name: str | None
    device_details: PitPatDeviceDetails
    tracking: PitPatTracking


def _get_location(data: Dict[str, Any]) -> Location:
    latitude=data.get('Latitude')
    longitude=data.get('Longitude')
    accuracy=data.get('Accuracy', {}).get('Metres')
    updated=data.get('DataTime')

    if latitude is None or longitude is None or accuracy is None:
        _LOGGER.warning('Missing one or more location properties: %s', data)
        return None

    return Location(
        updated=dateutil.parser.parse(updated),
        latitude=float(latitude),
        longitude=float(longitude),
        accuracy=float(accuracy),
    )


def map_dog_data(dog_data: Dict[str, Any], monitor_data: Dict[str, Any], activity_data: List[Dict[str, Any]]) -> PitPatDogData:
    raw_monitor_data = monitor_data.get('Value', {}).get('Monitor', {})
    latest_activity = sorted(activity_data, key=lambda item: item.get('Date'), reverse=True)[0] if len(activity_data) != 0 else None

    device_details = PitPatDeviceDetails(
        model_id=int(dog_data.get('Monitor', {}).get('Model', 0)),
        firmware_version=dog_data.get("Monitor", {}).get("FirmwareVersion", ""),
        hardware_version=dog_data.get("Monitor", {}).get("HardwareVersion", ""),
        serial_number=raw_monitor_data.get('SerialNumber'),
    )

    location = _get_location(raw_monitor_data.get('LastKnownPosition', {}).get('Value', {}))
    tracking = PitPatTracking(
        tracking_status=TrackingStatus(raw_monitor_data.get('GpsSynchronisationState', 0)),
        last_position=location,
    )

    return PitPatDogData(
        raw_dog_data=dog_data,
        raw_monitor_data=monitor_data.get('Value', {}).get('Monitor', {}),
        latest_raw_activity=latest_activity,

        name=dog_data.get('Name'),
        device_details=device_details,
        tracking=tracking,
    )

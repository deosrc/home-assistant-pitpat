from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
import logging
from typing import Any, Dict, List

import dateutil


_LOGGER = logging.getLogger(__name__)

class Gender(Enum):
    MALE = 0
    FEMALE = 1

class TrackingStatus(Enum):
    NOT_TRACKING = 0
    WAITING_FOR_CONNECTION = 1
    LISTENING_FOR_SATELLITES = 2
    TRACKING = 3

class TrackingMode(Enum):
    NONE = 0
    FIND_MY_DOG = 1
    WALK = 2

@dataclass(frozen=True, kw_only=True)
class Location():
    updated: datetime
    latitude: float
    longitude: float
    accuracy: float

@dataclass(frozen=True, kw_only=True)
class PitPatTracking():
    status: TrackingStatus | None
    mode: TrackingMode | None
    last_position: Location | None

@dataclass(frozen=True, kw_only=True)
class PitPatDevice():
    model_id: int
    firmware_version: str
    hardware_version: str
    serial_number: str

    is_charging: bool | None
    battery_level: float | None
    network_operator: str | None
    signal_strength: float | None
    tracking: PitPatTracking

    last_message_sent: datetime
    last_message_received: datetime
    next_message_expected: datetime

@dataclass(frozen=True, kw_only=True)
class PitPatDogData():
    raw_dog_data: Dict[str, Any]
    raw_monitor_data: Dict[str, Any]
    latest_raw_activity: Dict[str, Any] | None

    name: str | None
    breed_name: str | None
    breed_family: str | None
    gender: Gender
    date_of_birth: date | None
    weight: float | None
    device: PitPatDevice


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

    date_of_birth = dog_data.get('BirthDate')
    weight = dog_data.get('Weight')

    last_message_sent = raw_monitor_data.get('ContactTimings', {}).get('Value', {}).get('LastMessageSentAt')
    last_message_received = raw_monitor_data.get('ContactTimings', {}).get('Value', {}).get('LastMessageReceivedAt')
    next_message_expected = raw_monitor_data.get('ContactTimings', {}).get('Value', {}).get('NextMessageExpectedAt')

    location = _get_location(raw_monitor_data.get('LastKnownPosition', {}).get('Value', {}))
    tracking = PitPatTracking(
        status=TrackingStatus(raw_monitor_data.get('GpsSynchronisationState', 0)),
        mode=TrackingMode(raw_monitor_data.get('LiveTrackingReason', 0)),
        last_position=location,
    )

    device = PitPatDevice(
        model_id=int(dog_data.get('Monitor', {}).get('Model', 0)),
        firmware_version=dog_data.get("Monitor", {}).get("FirmwareVersion", ""),
        hardware_version=dog_data.get("Monitor", {}).get("HardwareVersion", ""),
        serial_number=raw_monitor_data.get('SerialNumber'),

        is_charging=bool(raw_monitor_data.get('BatteryInfo', {}).get('Value', {}).get('IsCharging', False)),
        battery_level=float(raw_monitor_data.get('BatteryInfo', {}).get('Value', {}).get('BatteryLevelFraction')),
        network_operator=raw_monitor_data.get('Network', {}).get('Value', {}).get('NetworkOperator', {}).get('Value'),
        signal_strength=float(raw_monitor_data.get('Network', {}).get('Value', {}).get('Quality')) / 5,
        tracking=tracking,

        last_message_sent=dateutil.parser.parse(last_message_sent),
        last_message_received=dateutil.parser.parse(last_message_received),
        next_message_expected=dateutil.parser.parse(next_message_expected),
    )

    return PitPatDogData(
        raw_dog_data=dog_data,
        raw_monitor_data=monitor_data.get('Value', {}).get('Monitor', {}),
        latest_raw_activity=latest_activity,

        name=dog_data.get('Name'),
        breed_name=dog_data.get('Breed', {}).get('Name'),
        breed_family=dog_data.get('Breed', {}).get('Family'),
        gender=Gender.FEMALE if dog_data.get('IsFemale') else Gender.MALE,
        date_of_birth=dateutil.parser.parse(date_of_birth).date() if date_of_birth else None,
        weight=float(weight) if weight else None,

        device=device,
    )

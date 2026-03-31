from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True, kw_only=True)
class PitPatDeviceDetails():
    model_id: int | None
    firmware_version: str | None
    hardware_version: str | None
    serial_number: str | None

@dataclass(frozen=True, kw_only=True)
class PitPatDogData():
    raw_dog_data: Dict[str, Any]
    raw_monitor_data: Dict[str, Any]
    latest_raw_activity: Dict[str, Any] | None

    name: str | None
    device_details: PitPatDeviceDetails


def map_dog_data( dog_data: Dict[str, Any], monitor_data: Dict[str, Any], activity_data: List[Dict[str, Any]]):
    raw_monitor_data = monitor_data.get('Value', {}).get('Monitor', {})
    latest_activity = sorted(activity_data, key=lambda item: item.get('Date'), reverse=True)[0] if len(activity_data) != 0 else None

    device_details = PitPatDeviceDetails(
        model_id=int(dog_data.get('Monitor', {}).get('Model', 0)),
        firmware_version=dog_data.get("Monitor", {}).get("FirmwareVersion", ""),
        hardware_version=dog_data.get("Monitor", {}).get("HardwareVersion", ""),
        serial_number=raw_monitor_data.get('SerialNumber'),
    )

    return PitPatDogData(
        raw_dog_data=dog_data,
        raw_monitor_data=monitor_data.get('Value', {}).get('Monitor', {}),
        latest_raw_activity=latest_activity,

        name=dog_data.get('Name'),
        device_details=device_details,
    )

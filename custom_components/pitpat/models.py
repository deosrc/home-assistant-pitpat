from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True, kw_only=True)
class PitPatDogData():
    raw_dog_data: Dict[str, Any]
    raw_monitor_data: Dict[str, Any]
    latest_raw_activity: Dict[str, Any] | None


def map_dog_data( dog_data: Dict[str, Any], monitor_data: Dict[str, Any], activity_data: List[Dict[str, Any]]):
    latest_activity = sorted(activity_data, key=lambda item: item.get('Date'), reverse=True)[0] if len(activity_data) != 0 else None

    return PitPatDogData(
        raw_dog_data=dog_data,
        raw_monitor_data=monitor_data.get('Value', {}).get('Monitor', {}),
        latest_raw_activity=latest_activity
    )

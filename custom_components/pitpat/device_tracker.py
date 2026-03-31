from dataclasses import dataclass
from typing import Any, Callable, Dict

import dateutil
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.device_tracker.config_entry import (
    TrackerEntity,
    TrackerEntityDescription
)

from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
)
from .coordinator import PitPatDataUpdateCoordinator
from .entity import PitPatDogEntity


def _get_monitor_position(entity: PitPatDogEntity) -> dict:
    return entity.data_monitor.get('LastKnownPosition', {}).get('Value', {})

def _is_tracking_live(entity: PitPatDogEntity) -> bool:
    return entity.data_monitor.get('GpsSynchronisationState', 0) == 3

@dataclass(frozen=True, kw_only=True)
class PitPatTrackerEntityDescription(TrackerEntityDescription):
    available_fn: Callable[[PitPatDogEntity], bool | None] = lambda data: True
    latitude_fn: Callable[[PitPatDogEntity], float | None]
    longitude_fn: Callable[[PitPatDogEntity], float | None]
    accuracy_fn: Callable[[PitPatDogEntity], float]
    attributes_fn: Callable[[PitPatDogEntity], dict | None] = None

ENTITY_DESCRIPTIONS = [
    PitPatTrackerEntityDescription(
        key='last_known_position',
        translation_key='last_known_position',
        icon="mdi:dog",
        latitude_fn=lambda entity: float(_get_monitor_position(entity).get('Latitude')),
        longitude_fn=lambda entity: float(_get_monitor_position(entity).get('Longitude')),
        accuracy_fn=lambda entity: float(_get_monitor_position(entity).get('Accuracy', {}).get('Metres')),
        attributes_fn=lambda entity: {
            "last_updated": dateutil.parser.parse(_get_monitor_position(entity).get('DataTime'))
        }
    ),
    PitPatTrackerEntityDescription(
        key='live_position',
        translation_key='live_position',
        icon="mdi:dog",
        available_fn=lambda data: _is_tracking_live(data),
        latitude_fn=lambda data: float(_get_monitor_position(data).get('Latitude')),
        longitude_fn=lambda data: float(_get_monitor_position(data).get('Longitude')),
        accuracy_fn=lambda data: float(_get_monitor_position(data).get('Accuracy', {}).get('Metres')),
    )
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.dogs.keys():
        for description in ENTITY_DESCRIPTIONS:
            sensors.append(PitPatDogDeviceTrackerEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatDogDeviceTrackerEntity(PitPatDogEntity, TrackerEntity):

    entity_description: PitPatTrackerEntityDescription

    _attr_has_entity_name = True

    @property
    def available(self) -> bool:
        try:
            return self.entity_description.available_fn(self)
        except Exception as e:
            raise ValueError(f"Unable to get availability value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def latitude(self) -> float | None:
        try:
            return self.entity_description.latitude_fn(self)
        except Exception as e:
            raise ValueError(f"Unable to get latitude value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def longitude(self) -> float | None:
        try:
            return self.entity_description.longitude_fn(self)
        except Exception as e:
            raise ValueError(f"Unable to get longitude value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def location_accuracy(self) -> float | None:
        try:
            return self.entity_description.accuracy_fn(self)
        except Exception as e:
            raise ValueError(f"Unable to get accuracy value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        try:
            attributes = super().extra_state_attributes
            if self.entity_description.attributes_fn:
                attributes = {**attributes, **self.entity_description.attributes_fn(self)}
            return attributes
        except Exception as e:
            raise ValueError(f"Unable to get attributes for {self.entity_description.key} sensor entity for dog id {self._dog_id}") from e

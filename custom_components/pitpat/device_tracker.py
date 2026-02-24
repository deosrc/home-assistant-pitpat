from dataclasses import dataclass
import logging
from typing import Any, Callable, Dict

import dateutil
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_IDENTIFIERS,
)
from homeassistant.components.device_tracker.config_entry import (
    TrackerEntity,
    TrackerEntityDescription
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
)
from .coordinator import PitPatDataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)


def _get_monitor(data: dict) -> dict:
    return data.get('monitor_details', {}).get('Value', {}).get('Monitor', {})

def _get_monitor_position(data: dict) -> dict:
    return _get_monitor(data).get('LastKnownPosition', {}).get('Value', {})

def _is_tracking_live(data: dict) -> bool:
    return _get_monitor(data).get('GpsSynchronisationState', 0) == 3

@dataclass(frozen=True, kw_only=True)
class PitPatTrackerEntityDescription(TrackerEntityDescription):
    available_fn: Callable[[dict], bool | None] = lambda data: True
    latitude_fn: Callable[[dict], float | None]
    longitude_fn: Callable[[dict], float | None]
    accuracy_fn: Callable[[dict], float]
    attributes_fn: Callable[[dict], dict | None] = None

ENTITY_DESCRIPTIONS = [
    PitPatTrackerEntityDescription(
        key='last_known_position',
        translation_key='last_known_position',
        icon="mdi:dog",
        latitude_fn=lambda data: float(_get_monitor_position(data).get('Latitude')),
        longitude_fn=lambda data: float(_get_monitor_position(data).get('Longitude')),
        accuracy_fn=lambda data: float(_get_monitor_position(data).get('Accuracy', {}).get('Metres')),
        attributes_fn=lambda data: {
            "last_updated": dateutil.parser.parse(_get_monitor_position(data).get('DataTime'))
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

class PitPatDogDeviceTrackerEntity(CoordinatorEntity[PitPatDataUpdateCoordinator], TrackerEntity):

    _attr_has_entity_name = True

    def __init__(self, coordinator: PitPatDataUpdateCoordinator, dog_id: str, description: PitPatTrackerEntityDescription):
        CoordinatorEntity.__init__(self, coordinator)
        self._dog_id = dog_id
        self.entity_description = description

        # Required for HA 2022.7
        self.coordinator_context = object()

    @property
    def unique_id(self) -> str:
        return f'{self._dog_id}-{self.entity_description.key}'

    @property
    def description(self) -> PitPatTrackerEntityDescription:
        return self.entity_description

    @property
    def data(self):
        return self.coordinator.dogs.get(self._dog_id)

    @property
    def available(self) -> bool:
        try:
            return self.description.available_fn(self.data)
        except Exception as e:
            raise ValueError(f"Unable to get availability value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def latitude(self) -> float | None:
        try:
            return self.description.latitude_fn(self.data)
        except Exception as e:
            raise ValueError(f"Unable to get latitude value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def longitude(self) -> float | None:
        try:
            return self.description.longitude_fn(self.data)
        except Exception as e:
            raise ValueError(f"Unable to get longitude value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def location_accuracy(self) -> float | None:
        try:
            return self.description.accuracy_fn(self.data)
        except Exception as e:
            raise ValueError(f"Unable to get accuracy value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def base_attributes(self) -> Dict[str, Any] | None:
        return {
            "dog_id": self._dog_id,
        }

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        try:
            attributes = self.base_attributes
            if self.description.attributes_fn:
                attributes = {**attributes, **self.description.attributes_fn(self.data)}
            return attributes
        except Exception as e:
            raise ValueError(f"Unable to get attributes for {self.entity_description.key} sensor entity for dog id {self._dog_id}") from e

    @property
    def device_info(self):
        """Return device information about this device."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._dog_id)}
        }

import logging
from typing import Any, Dict

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

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.dogs.keys():
        sensors.append(PitPatDogDeviceTrackerEntity(coordinator, dog_id))

    async_add_entities(sensors, True)

class PitPatDogDeviceTrackerEntity(CoordinatorEntity[PitPatDataUpdateCoordinator], TrackerEntity):

    def __init__(self, coordinator: PitPatDataUpdateCoordinator, dog_id: str):
        CoordinatorEntity.__init__(self, coordinator)
        self._dog_id = dog_id

        self.entity_description = TrackerEntityDescription(
            key='tracker',
            translation_key='tracker',
            icon="mdi:dog"
        )

        # Required for HA 2022.7
        self.coordinator_context = object()

    @property
    def unique_id(self) -> str:
        return f'{self._dog_id}-{self.entity_description.key}'

    @property
    def data(self):
        return self.coordinator.dogs.get(self._dog_id)

    @property
    def latitude(self):
        try:
            return _get_monitor(self.data).get('LastKnownPosition', {}).get('Value', {}).get('Latitude')
        except Exception as e:
            raise ValueError(f"Unable to get latitude value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def longitude(self):
        try:
            return _get_monitor(self.data).get('LastKnownPosition', {}).get('Value', {}).get('Longitude')
        except Exception as e:
            raise ValueError(f"Unable to get longitude value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def location_accuracy(self):
        try:
            return _get_monitor(self.data).get('LastKnownPosition', {}).get('Value', {}).get('Accuracy', {}).get('Metres')
        except Exception as e:
            raise ValueError(f"Unable to get accuracy value for {self.entity_description.key} device tracker entity for dog id {self._dog_id}") from e

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        try:
            return {
                "dog_id": self._dog_id,
                "last_updated": dateutil.parser.parse(_get_monitor(self.data).get('LastKnownPosition', {}).get('Value', {}).get('DataTime'))
            }
        except Exception as e:
            raise ValueError(f"Unable to get attributes for {self.entity_description.key} sensor entity for dog id {self._dog_id}") from e

    @property
    def device_info(self):
        """Return device information about this device."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._dog_id)}
        }

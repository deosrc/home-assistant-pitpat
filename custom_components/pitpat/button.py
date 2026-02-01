from dataclasses import dataclass
import logging
from typing import Callable

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_IDENTIFIERS,
)
from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import PitPatApiClient
from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
)
from .coordinator import PitPatDataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class PitPatButtonEntityDescription(ButtonEntityDescription):
    press_fn: Callable[[PitPatApiClient, str], None]

DOG_ENTITY_DESCRIPTIONS = [
    PitPatButtonEntityDescription(
        key="tracking_stop",
        translation_key="tracking_stop",
        press_fn=lambda api, dog_id: api.async_tracking_stop(dog_id)
    ),
    PitPatButtonEntityDescription(
        key="tracking_start_find",
        translation_key="tracking_start_find",
        press_fn=lambda api, dog_id: api.async_tracking_start_find(dog_id)
    ),
    PitPatButtonEntityDescription(
        key="tracking_start_walk",
        translation_key="tracking_start_walk",
        press_fn=lambda api, dog_id: api.async_tracking_start_walk(dog_id)
    ),
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.dogs.keys():
        for description in DOG_ENTITY_DESCRIPTIONS:
            sensors.append(PitPatDogButtonEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatDogButtonEntity(CoordinatorEntity[PitPatDataUpdateCoordinator], ButtonEntity):

    _attr_has_entity_name = True # Required for reading translation_key from EntityDescription

    def __init__(self, coordinator: PitPatDataUpdateCoordinator, dog_id: str, description: PitPatButtonEntityDescription):
        CoordinatorEntity.__init__(self, coordinator)
        self._dog_id = dog_id
        self.entity_description = description

        # Required for HA 2022.7
        self.coordinator_context = object()

    @property
    def unique_id(self) -> str:
        return f'{self._dog_id}-{self.description.key}'

    @property
    def description(self) -> PitPatButtonEntityDescription:
        return self.entity_description

    @property
    def device_info(self):
        """Return device information about this device."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._dog_id)},
        }

    async def async_press(self):
        await self.description.press_fn(self.coordinator.api_client, self._dog_id)
        await self.coordinator.async_refresh()

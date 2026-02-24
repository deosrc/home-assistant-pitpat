from dataclasses import dataclass
from typing import Any, Callable, Dict

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_IDENTIFIERS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from propcache import cached_property

from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
)
from .coordinator import PitPatDataUpdateCoordinator


def _get_monitor(data: dict) -> dict:
    return data.get('monitor_details', {}).get('Value', {}).get('Monitor', {})

@dataclass(frozen=True, kw_only=True)
class PitPatSelectEntityDescription(SelectEntityDescription):
    current_option_fn: Callable[[dict], str | None]
    attributes_fn: Callable[[dict], dict | None] = None

ENTITY_DESCRIPTIONS = [
    PitPatSelectEntityDescription(
        key='phone_home_cadence',
        translation_key='phone_home_cadence',
        icon='mdi:mail-fast-outline',
        options=['0','1','2'],
        current_option_fn=lambda data: _get_monitor(data).get('PhoneHomeCadence', 1)
    )
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.dogs.keys():
        for description in ENTITY_DESCRIPTIONS:
            sensors.append(PitPatSelectEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatSelectEntity(CoordinatorEntity[PitPatDataUpdateCoordinator], SelectEntity):

    _attr_has_entity_name = True # Required for reading translation_key from EntityDescription

    def __init__(self, coordinator: PitPatDataUpdateCoordinator, dog_id: str, description: PitPatSelectEntityDescription):
        CoordinatorEntity.__init__(self, coordinator)
        self._dog_id = dog_id
        self.entity_description = description

        # Required for HA 2022.7
        self.coordinator_context = object()

    @property
    def unique_id(self) -> str:
        return f'{self._dog_id}-{self.description.key}'

    @property
    def description(self) -> PitPatSelectEntityDescription:
        return self.entity_description

    @property
    def data(self):
        return self.coordinator.dogs.get(self._dog_id)

    @cached_property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        try:
            return str(self.description.current_option_fn(self.data))
        except Exception as e:
            raise ValueError(f"Unable to get value for {self.entity_description.key} select entity for dog id {self._dog_id}") from e

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
            ATTR_IDENTIFIERS: {(DOMAIN, self._dog_id)},
        }

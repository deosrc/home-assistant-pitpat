from dataclasses import dataclass
from typing import Any, Callable, Dict

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from propcache import cached_property

from .api import PitPatApiClient
from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
    PHONE_HOME_CADENCE_MAP,
)
from .coordinator import PitPatDataUpdateCoordinator
from .entity import PitPatDogEntity


def _get_phone_home_cadence(entity: PitPatDogEntity) -> str | None:
    raw_value = entity.data_dog.get('PhoneHomeCadence', 1)
    return PHONE_HOME_CADENCE_MAP.get(raw_value, PHONE_HOME_CADENCE_MAP[1])

@dataclass(frozen=True, kw_only=True)
class PitPatSelectEntityDescription(SelectEntityDescription):
    current_option_fn: Callable[[PitPatDogEntity], str | None]
    attributes_fn: Callable[[PitPatDogEntity], dict | None] = None
    update_fn: Callable[[PitPatApiClient, PitPatDogEntity, str], None]

ENTITY_DESCRIPTIONS = [
    PitPatSelectEntityDescription(
        key='phone_home_cadence',
        translation_key='phone_home_cadence',
        icon='mdi:email-fast-outline',
        entity_category=EntityCategory.CONFIG,
        options=list(PHONE_HOME_CADENCE_MAP.values()),
        current_option_fn=lambda entity: _get_phone_home_cadence(entity),
        update_fn=lambda api, entity, option: api.async_update_phone_home_cadence(entity.dog_id, option),
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

class PitPatSelectEntity(PitPatDogEntity, SelectEntity):

    _attr_has_entity_name = True # Required for reading translation_key from EntityDescription

    @property
    def description(self) -> PitPatSelectEntityDescription:
        return self.entity_description

    @cached_property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        try:
            return str(self.description.current_option_fn(self))
        except Exception as e:
            raise ValueError(f"Unable to get value for {self.entity_description.key} select entity for dog id {self.dog_id}") from e

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        try:
            attributes = super().extra_state_attributes
            if self.description.attributes_fn:
                attributes = {**attributes, **self.description.attributes_fn(self)}
            return attributes
        except Exception as e:
            raise ValueError(f"Unable to get attributes for {self.entity_description.key} sensor entity for dog id {self.dog_id}") from e

    async def async_select_option(self, option: str):
        try:
            await self.description.update_fn(self.coordinator.api_client, self, option)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            raise HomeAssistantError(f'Failed to update phone home cadence.') from err

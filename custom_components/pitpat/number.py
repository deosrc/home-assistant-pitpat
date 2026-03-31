from dataclasses import dataclass
import logging
from typing import Any, Callable, Dict

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .api import PitPatApiClient
from .const import DATA_KEY_COORDINATOR, DOMAIN
from .coordinator import PitPatDataUpdateCoordinator
from .entity import PitPatDogEntity


_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class PitPatNumberEntityDescription(NumberEntityDescription):
    value_fn: Callable[[PitPatDogEntity], int | float | None]
    attributes_fn: Callable[[PitPatDogEntity], dict | None] = None
    set_fn: Callable[[PitPatApiClient, PitPatDogEntity, float], None]


DOG_ENTITY_DESCRIPTIONS = [
    PitPatNumberEntityDescription(
        key='weight',
        translation_key='weight',
        device_class=NumberDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS, # TODO: Make sure this is correct based on user settings
        mode=NumberMode.BOX,
        native_step=0.1,
        native_min_value=1.0,
        native_max_value=150.0,
        value_fn=lambda entity: entity.data_dog.get('Weight'),
        set_fn=lambda api, entity, value: api.async_set_weight(entity.dog_id, value)
    )
]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.dogs.keys():
        for description in DOG_ENTITY_DESCRIPTIONS:
            sensors.append(PitPatDogNumberEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatDogNumberEntity(PitPatDogEntity, NumberEntity):

    _attr_has_entity_name = True # Required for reading translation_key from EntityDescription
    entity_description: PitPatNumberEntityDescription

    @property
    def native_value(self):
        try:
            return self.entity_description.value_fn(self)
        except Exception as e:
            raise ValueError(f"Unable to get value for {self.entity_description.key} number entity for dog id {self.dog_id}") from e

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        try:
            attributes = super().extra_state_attributes
            if self.entity_description.attributes_fn:
                attributes = {**attributes, **self.entity_description.attributes_fn(self)}
            return attributes
        except Exception as e:
            raise ValueError(f"Unable to get attributes for {self.entity_description.key} number entity for dog id {self.dog_id}") from e

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self.entity_description.set_fn(self.coordinator.api_client, self, value)
            await self.coordinator.async_request_refresh()
        except Exception as e:
            raise HomeAssistantError(f'Failed to update {self.entity_description.key} number entity for dog id {self.dog_id}') from e

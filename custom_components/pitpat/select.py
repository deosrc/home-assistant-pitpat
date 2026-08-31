from dataclasses import dataclass
import logging
from typing import Any, Callable, Dict, List

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .api import PitPatApiClient
from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
    PHONE_HOME_CADENCE_MAP,
    Device,
)
from .coordinator import PitPatDataUpdateCoordinator
from .entity import PitPatDogEntity


_LOGGER = logging.getLogger(__name__)

def _get_phone_home_cadence_raw(entity: PitPatDogEntity) -> str | None:
    return entity.data_monitor.get('PhoneHomeCadence')

def _get_phone_home_cadence(entity: PitPatDogEntity) -> str | None:
    raw_value = _get_phone_home_cadence_raw(entity)
    if raw_value == None:
        # Activity monitors do not report a cadence, so this is expected rather
        # than exceptional on those devices.
        _LOGGER.debug('No cadence available.')
        return None

    option_value = PHONE_HOME_CADENCE_MAP.get(raw_value)
    if option_value == None:
        _LOGGER.error('No cadence mapping available for value "%s"', raw_value)
        return None

    _LOGGER.debug('Cadence value "%s" converted to option "%s"', raw_value, option_value)
    return option_value

@dataclass(frozen=True, kw_only=True)
class PitPatSelectEntityDescription(SelectEntityDescription):
    current_option_fn: Callable[[PitPatDogEntity], str | None]
    attributes_fn: Callable[[PitPatDogEntity], dict | None] = None
    update_fn: Callable[[PitPatApiClient, PitPatDogEntity, str], None]

    # The devices the sensor is applicable to. If not provided, sensor will be created for all devices.
    applicable_devices: List[Device] = None

ENTITY_DESCRIPTIONS = [
    PitPatSelectEntityDescription(
        key='phone_home_cadence',
        translation_key='phone_home_cadence',
        icon='mdi:email-fast-outline',
        entity_category=EntityCategory.CONFIG,
        options=list(PHONE_HOME_CADENCE_MAP.values()),
        current_option_fn=lambda entity: _get_phone_home_cadence(entity),
        attributes_fn=lambda entity: {
            'raw_value': _get_phone_home_cadence_raw(entity)
        },
        update_fn=lambda api, entity, option: api.async_update_phone_home_cadence(entity.dog_id, option),
        applicable_devices=[Device.GpsTracker]
    )
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.data.keys():
        device = Device(coordinator.data.get(dog_id, {}).get('Monitor', {}).get('Model'))
        for description in ENTITY_DESCRIPTIONS:
            if not description.applicable_devices or device in description.applicable_devices:
                sensors.append(PitPatSelectEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatSelectEntity(PitPatDogEntity[PitPatSelectEntityDescription], SelectEntity):

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        try:
            value = self.entity_description.current_option_fn(self)
            # str(None) is "None", which is not a valid option, so Home Assistant
            # raises every time the state is written.
            return None if value is None else str(value)
        except Exception as e:
            raise ValueError(f"Unable to get value for {self.entity_description.key} select entity for dog id {self.dog_id}") from e

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        try:
            attributes = super().extra_state_attributes
            if self.entity_description.attributes_fn:
                attributes = {**attributes, **self.entity_description.attributes_fn(self)}
            return attributes
        except Exception as e:
            raise ValueError(f"Unable to get attributes for {self.entity_description.key} sensor entity for dog id {self.dog_id}") from e

    async def async_select_option(self, option: str):
        try:
            await self.entity_description.update_fn(self.coordinator.api_client, self, option)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            raise HomeAssistantError(f'Failed to update phone home cadence.') from err

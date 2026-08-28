from dataclasses import dataclass
from typing import Callable, List

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)

from .api import PitPatApiClient
from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
    Device,
)
from .coordinator import PitPatDataUpdateCoordinator
from .entity import PitPatDogEntity


@dataclass(frozen=True, kw_only=True)
class PitPatButtonEntityDescription(ButtonEntityDescription):
    press_fn: Callable[[PitPatApiClient, PitPatDogEntity], None]

    # The devices the sensor is applicable to. If not provided, sensor will be created for all devices.
    applicable_devices: List[Device] = None

DOG_ENTITY_DESCRIPTIONS = [
    PitPatButtonEntityDescription(
        key="tracking_stop",
        translation_key="tracking_stop",
        press_fn=lambda api, entity: api.async_tracking_stop(entity.dog_id),
        applicable_devices=[Device.GpsTracker],
    ),
    PitPatButtonEntityDescription(
        key="tracking_start_find",
        translation_key="tracking_start_find",
        press_fn=lambda api, entity: api.async_tracking_start_find(entity.dog_id),
        applicable_devices=[Device.GpsTracker],
    ),
    PitPatButtonEntityDescription(
        key="tracking_start_walk",
        translation_key="tracking_start_walk",
        press_fn=lambda api, entity: api.async_tracking_start_walk(entity.dog_id),
        applicable_devices=[Device.GpsTracker],
    ),
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.data.keys():
        device = Device(coordinator.data.get(dog_id, {}).get('Monitor', {}).get('Model'))
        for description in DOG_ENTITY_DESCRIPTIONS:
            if not description.applicable_devices or device in description.applicable_devices:
                sensors.append(PitPatDogButtonEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatDogButtonEntity(PitPatDogEntity[PitPatButtonEntityDescription], ButtonEntity):

    async def async_press(self):
        await self.entity_description.press_fn(self.coordinator.api_client, self)
        await self.coordinator.async_refresh()

from dataclasses import dataclass
from typing import Any, Callable, Dict

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
from .models import TrackingStatus


@dataclass(frozen=True, kw_only=True)
class PitPatTrackerEntityDescription(TrackerEntityDescription):
    available_fn: Callable[[PitPatDogEntity], bool | None] = lambda entity: True
    attributes_fn: Callable[[PitPatDogEntity], dict | None] = None

ENTITY_DESCRIPTIONS = [
    PitPatTrackerEntityDescription(
        key='last_known_position',
        translation_key='last_known_position',
        icon="mdi:dog",
        attributes_fn=lambda entity: {
            "last_updated": entity.data.device.tracking.last_position.updated
        }
    ),
    PitPatTrackerEntityDescription(
        key='live_position',
        translation_key='live_position',
        icon="mdi:dog",
        available_fn=lambda entity: entity.data.device.tracking.status == TrackingStatus.TRACKING,
    )
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.data.keys():
        for description in ENTITY_DESCRIPTIONS:
            sensors.append(PitPatDogDeviceTrackerEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatDogDeviceTrackerEntity(PitPatDogEntity[PitPatTrackerEntityDescription], TrackerEntity):

    @property
    def available(self) -> bool:
        try:
            if not self.data.device.tracking.last_position:
                return False

            return self.entity_description.available_fn(self)
        except Exception as e:
            raise ValueError(f"Unable to get availability value for {self.entity_description.key} device tracker entity for dog id {self.dog_id}") from e

    @property
    def latitude(self) -> float | None:
        try:
            return self.data.device.tracking.last_position.latitude
        except Exception as e:
            raise ValueError(f"Unable to get latitude value for {self.entity_description.key} device tracker entity for dog id {self.dog_id}") from e

    @property
    def longitude(self) -> float | None:
        try:
            return self.data.device.tracking.last_position.longitude
        except Exception as e:
            raise ValueError(f"Unable to get longitude value for {self.entity_description.key} device tracker entity for dog id {self.dog_id}") from e

    @property
    def location_accuracy(self) -> float | None:
        try:
            return self.data.device.tracking.last_position.accuracy
        except Exception as e:
            raise ValueError(f"Unable to get accuracy value for {self.entity_description.key} device tracker entity for dog id {self.dog_id}") from e

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        try:
            attributes = super().extra_state_attributes
            if self.entity_description.attributes_fn:
                attributes = {**attributes, **self.entity_description.attributes_fn(self)}
            return attributes
        except Exception as e:
            raise ValueError(f"Unable to get attributes for {self.entity_description.key} sensor entity for dog id {self.dog_id}") from e

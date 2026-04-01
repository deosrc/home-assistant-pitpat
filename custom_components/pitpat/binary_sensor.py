from dataclasses import dataclass
from typing import Any, Callable, Dict

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
)
from .coordinator import PitPatDataUpdateCoordinator
from .entity import PitPatDogEntity
from .models import TrackingMode


@dataclass(frozen=True, kw_only=True)
class PitPatBinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[PitPatDogEntity], str | int | float | None]
    attributes_fn: Callable[[PitPatDogEntity], dict | None] = None

DOG_ENTITY_DESCRIPTIONS = [
    PitPatBinarySensorEntityDescription(
        key="live_tracking_active",
        translation_key="live_tracking_active",
        value_fn=lambda entity: entity.data.tracking.tracking_mode != TrackingMode.NONE,
    ),
    PitPatBinarySensorEntityDescription(
        key="charging_status",
        translation_key="charging_status",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda entity: bool(entity.data_monitor.get('BatteryInfo', {}).get('Value', {}).get('IsCharging', False)),
    ),
    PitPatBinarySensorEntityDescription(
        key='user_goal_achieved',
        translation_key='user_goal_achieved',
        icon="mdi:flag-checkered",
        value_fn=lambda entity: bool(entity.data.latest_raw_activity.get('UserGoalAchieved', False))
    )
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.data.keys():
        for description in DOG_ENTITY_DESCRIPTIONS:
            sensors.append(PitPatDogBinarySensorEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatDogBinarySensorEntity(PitPatDogEntity[PitPatBinarySensorEntityDescription], BinarySensorEntity):

    @property
    def is_on(self):
        try:
            return self.entity_description.value_fn(self)
        except Exception as e:
            raise ValueError(f"Unable to get value for {self.entity_description.key} binary sensor entity for dog id {self.dog_id}") from e

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        try:
            attributes = super().extra_state_attributes
            if self.entity_description.attributes_fn:
                attributes = {**attributes, **self.entity_description.attributes_fn(self)}
            return attributes
        except Exception as e:
            raise ValueError(f"Unable to get attributes for {self.entity_description.key} sensor entity for dog id {self.dog_id}") from e

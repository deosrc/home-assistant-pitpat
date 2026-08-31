from dataclasses import dataclass
from typing import Any, Callable, Dict, List

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
    Device,
)
from .coordinator import PitPatDataUpdateCoordinator
from .entity import PitPatDogEntity


@dataclass(frozen=True, kw_only=True)
class PitPatBinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[PitPatDogEntity], str | int | float | None]
    attributes_fn: Callable[[PitPatDogEntity], dict | None] = None

    # The devices the sensor is applicable to. If not provided, sensor will be created for all devices.
    applicable_devices: List[Device] = None

DOG_ENTITY_DESCRIPTIONS = [
    PitPatBinarySensorEntityDescription(
        key="live_tracking_active",
        translation_key="live_tracking_active",
        value_fn=lambda entity: entity.data_monitor.get('LiveTrackingReason', 0) != 0,
        applicable_devices=[Device.GpsTracker],
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
        value_fn=lambda entity: bool(entity.data_dog.get('activity_today', {}).get('UserGoalAchieved', False))
    )
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.data.keys():
        device = Device(coordinator.data.get(dog_id, {}).get('Monitor', {}).get('Model'))
        for description in DOG_ENTITY_DESCRIPTIONS:
            if not description.applicable_devices or device in description.applicable_devices:
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

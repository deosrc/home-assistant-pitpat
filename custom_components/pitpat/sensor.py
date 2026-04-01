from dataclasses import dataclass
from typing import Any, Callable, Dict

import dateutil
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfMass,
    UnitOfTime,
    PERCENTAGE,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
)
from .coordinator import PitPatDataUpdateCoordinator
from .entity import PitPatDogEntity


@dataclass(frozen=True, kw_only=True)
class PitPatSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[PitPatDogEntity], str | int | float | None]
    attributes_fn: Callable[[PitPatDogEntity], dict | None] = None

DOG_ENTITY_DESCRIPTIONS = [
    PitPatSensorEntityDescription(
        key="breed",
        translation_key="breed",
        icon="mdi:dog-side",
        value_fn=lambda entity: entity.data.breed_name,
    ),
    PitPatSensorEntityDescription(
        key="family",
        translation_key="family",
        icon="mdi:dog-side",
        value_fn=lambda entity: entity.data.breed_family,
    ),
    PitPatSensorEntityDescription(
        key="gender",
        translation_key="gender",
        icon="mdi:gender-male-female",
        value_fn=lambda entity: entity.data.gender.name.lower(),
    ),
    PitPatSensorEntityDescription(
        key="date_of_birth",
        translation_key="date_of_birth",
        icon="mdi:calendar",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda entity: entity.data.date_of_birth,
    ),
    PitPatSensorEntityDescription(
        key="weight",
        translation_key="weight",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS, # TODO: Make sure this is correct based on user settings
        suggested_display_precision=1,
        value_fn=lambda entity: entity.data.weight,
    ),
    PitPatSensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda entity: entity.data.device.battery_level * 100,
    ),
    PitPatSensorEntityDescription(
        key="network",
        translation_key="network",
        icon='mdi:radio-tower',
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda entity: entity.data.device.network_operator,
    ),
    PitPatSensorEntityDescription(
        key="signal_strength",
        translation_key="signal_strength",
        icon='mdi:signal',
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda entity: entity.data.device.signal_strength * 100,
    ),
    PitPatSensorEntityDescription(
        key="last_message_sent",
        translation_key="last_message_sent",
        icon="mdi:email-arrow-right-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda entity: entity.data.device.last_message_sent,
    ),
    PitPatSensorEntityDescription(
        key="last_message_received",
        translation_key="last_message_received",
        icon="mdi:email-arrow-left-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda entity: entity.data.device.last_message_received,
    ),
    PitPatSensorEntityDescription(
        key="next_message_expected",
        translation_key="next_message_expected",
        icon="mdi:email-fast-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda entity: entity.data.device.next_message_expected,
    ),
    PitPatSensorEntityDescription(
        key="activity_pottering",
        translation_key="activity_pottering",
        icon="mdi:dog",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda entity: entity.data.latest_raw_activity.get('TotalPotteringMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_running",
        translation_key="activity_running",
        icon="mdi:run-fast",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda entity: entity.data.latest_raw_activity.get('TotalRunMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_walking",
        translation_key="activity_walking",
        icon="mdi:walk",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda entity: entity.data.latest_raw_activity.get('TotalWalkMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_playing",
        translation_key="activity_playing",
        icon="mdi:tennis-ball",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda entity: entity.data.latest_raw_activity.get('TotalPlayMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_resting",
        translation_key="activity_resting",
        icon="mdi:sleep",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda entity: entity.data.latest_raw_activity.get('TotalRestMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_total_exercising",
        translation_key="activity_total_exercising",
        icon="mdi:run",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda entity: entity.data.latest_raw_activity.get('Activeness', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_steps",
        translation_key="activity_steps",
        icon="mdi:paw",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="steps",
        value_fn=lambda entity: entity.data.latest_raw_activity.get('TotalSteps', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_distance",
        translation_key="activity_distance",
        icon="mdi:map-marker-distance",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=0,
        value_fn=lambda entity: entity.data.latest_raw_activity.get('TotalDistance', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_calories",
        translation_key="activity_calories",
        icon="mdi:fire",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_CALORIE,
        value_fn=lambda entity: entity.data.latest_raw_activity.get('TotalCalories', 0),
    ),
    PitPatSensorEntityDescription(
        key="user_goal_progress",
        translation_key="user_goal_progress",
        icon="mdi:flag-checkered",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda entity: (entity.data.latest_raw_activity.get('Activeness', 0) / entity.data.latest_raw_activity.get('UserGoal', 0)) * 100,
    ),
    PitPatSensorEntityDescription(
        key="live_tracking_mode",
        translation_key="live_tracking_mode",
        icon="mdi:map-marker-radius",
        value_fn=lambda entity: entity.data.device.tracking.mode.name.lower(),
    ),
    PitPatSensorEntityDescription(
        key="live_tracking_status",
        translation_key="live_tracking_status",
        icon="mdi:satellite-variant",
        value_fn=lambda entity: entity.data.device.tracking.status.name.lower(),
    ),
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.data.keys():
        for description in DOG_ENTITY_DESCRIPTIONS:
            sensors.append(PitPatDogSensorEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatDogSensorEntity(PitPatDogEntity[PitPatSensorEntityDescription], SensorEntity):

    @property
    def native_value(self):
        try:
            return self.entity_description.value_fn(self)
        except Exception as e:
            raise ValueError(f"Unable to get value for {self.entity_description.key} sensor entity for dog id {self.dog_id}") from e

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        try:
            attributes = super().extra_state_attributes
            if self.entity_description.attributes_fn:
                attributes = {**attributes, **self.entity_description.attributes_fn(self)}
            return attributes
        except Exception as e:
            raise ValueError(f"Unable to get attributes for {self.entity_description.key} sensor entity for dog id {self.dog_id}") from e

from dataclasses import dataclass
import logging
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
    ATTR_IDENTIFIERS,
    ATTR_NAME,
    ATTR_MANUFACTURER,
    ATTR_SW_VERSION,
    ATTR_HW_VERSION,
    ATTR_SERIAL_NUMBER,
    PERCENTAGE,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import PitPatDataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)

def _get_monitor(data: dict) -> dict:
    return data.get('monitor_details', {}).get('Value', {}).get('Monitor', {})

def _get_tracking_mode(data: dict):
    monitor = _get_monitor(data)
    reason_id = monitor.get('LiveTrackingReason', 0)
    if reason_id == 1:
        return 'Find my dog'
    elif reason_id == 2:
        return 'Walk'
    else:
        return 'None'

def _get_tracking_status(data: dict):
    monitor = _get_monitor(data)
    reason_id = monitor.get('GpsSynchronisationState', 0)
    if reason_id == 0:
        return 'Not tracking'
    elif reason_id == 1:
        return 'Waiting for connection'
    elif reason_id == 2:
        return 'Listening for satellites'
    elif reason_id == 3:
        return 'Tracking'
    else:
        return 'unknown'

@dataclass(frozen=True, kw_only=True)
class PitPatSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict], str | int | float | None]
    attributes_fn: Callable[[dict], dict | None] = None

DOG_ENTITY_DESCRIPTIONS = [
    PitPatSensorEntityDescription(
        key="breed",
        translation_key="breed",
        icon="mdi:dog-side",
        value_fn=lambda data: data.get('Breed', {}).get('Name'),
    ),
    PitPatSensorEntityDescription(
        key="family",
        translation_key="family",
        icon="mdi:dog-side",
        value_fn=lambda data: data.get('Breed', {}).get('Family'),
    ),
    PitPatSensorEntityDescription(
        key="gender",
        translation_key="gender",
        icon="mdi:gender-male-female",
        value_fn=lambda data: 'Female' if data.get('IsFemale', {}) else 'Male',
    ),
    PitPatSensorEntityDescription(
        key="date_of_birth",
        translation_key="date_of_birth",
        icon="mdi:calendar",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda data: dateutil.parser.parse(data.get('BirthDate')).date(),
    ),
    PitPatSensorEntityDescription(
        key="weight",
        translation_key="weight",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS, # TODO: Make sure this is correct based on user settings
        suggested_display_precision=1,
        value_fn=lambda data: data.get('Weight'),
    ),
    PitPatSensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda data: _get_monitor(data).get('BatteryInfo', {}).get('Value', {}).get('BatteryLevelFraction') * 100,
    ),
    PitPatSensorEntityDescription(
        key="network",
        translation_key="network",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _get_monitor(data).get('Network', {}).get('Value', {}).get('NetworkOperator', {}).get('Value'),
    ),
    PitPatSensorEntityDescription(
        key="signal_strength",
        translation_key="signal_strength",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda data: _get_monitor(data).get('Network', {}).get('Value', {}).get('Quality') * 20,
    ),
    PitPatSensorEntityDescription(
        key="last_message_sent",
        translation_key="last_message_sent",
        icon="mdi:email-arrow-right-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: dateutil.parser.parse(_get_monitor(data).get('ContactTimings', {}).get('Value', {}).get('LastMessageSentAt')),
    ),
    PitPatSensorEntityDescription(
        key="last_message_received",
        translation_key="last_message_received",
        icon="mdi:email-arrow-left-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: dateutil.parser.parse(_get_monitor(data).get('ContactTimings', {}).get('Value', {}).get('LastMessageReceivedAt')),
    ),
    PitPatSensorEntityDescription(
        key="next_message_expected",
        translation_key="next_message_expected",
        icon="mdi:email-fast-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: dateutil.parser.parse(_get_monitor(data).get('ContactTimings', {}).get('Value', {}).get('NextMessageExpectedAt')),
    ),
    PitPatSensorEntityDescription(
        key="activity_pottering",
        translation_key="activity_pottering",
        icon="mdi:dog",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda data: data.get('activity_today', {}).get('TotalPotteringMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_running",
        translation_key="activity_running",
        icon="mdi:run-fast",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data: data.get('activity_today', {}).get('TotalRunMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_walking",
        translation_key="activity_walking",
        icon="mdi:walk",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data: data.get('activity_today', {}).get('TotalWalkMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_playing",
        translation_key="activity_playing",
        icon="mdi:tennis-ball",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data: data.get('activity_today', {}).get('TotalPlayMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_resting",
        translation_key="activity_resting",
        icon="mdi:sleep",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda data: data.get('activity_today', {}).get('TotalRestMinutes', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_total_exercising",
        translation_key="activity_total_exercising",
        icon="mdi:run",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data: data.get('activity_today', {}).get('Activeness', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_steps",
        translation_key="activity_steps",
        icon="mdi:paw",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="steps",
        value_fn=lambda data: data.get('activity_today', {}).get('TotalSteps', 0),
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
        value_fn=lambda data: data.get('activity_today', {}).get('TotalDistance', 0),
    ),
    PitPatSensorEntityDescription(
        key="activity_calories",
        translation_key="activity_calories",
        icon="mdi:fire",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_CALORIE,
        value_fn=lambda data: data.get('activity_today', {}).get('TotalCalories', 0),
    ),
    PitPatSensorEntityDescription(
        key="live_tracking_mode",
        translation_key="live_tracking_mode",
        icon="mdi:map-marker-radius",
        value_fn=lambda data: _get_tracking_mode(data),
    ),
    PitPatSensorEntityDescription(
        key="live_tracking_status",
        translation_key="live_tracking_status",
        icon="mdi:satellite-variant",
        value_fn=lambda data: _get_tracking_status(data),
    ),
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.dogs.keys():
        for description in DOG_ENTITY_DESCRIPTIONS:
            sensors.append(PitPatDogSensorEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatDogSensorEntity(CoordinatorEntity[PitPatDataUpdateCoordinator], SensorEntity):

    _attr_has_entity_name = True # Required for reading translation_key from EntityDescription

    def __init__(self, coordinator: PitPatDataUpdateCoordinator, dog_id: str, description: PitPatSensorEntityDescription):
        CoordinatorEntity.__init__(self, coordinator)
        self._dog_id = dog_id
        self.entity_description = description

        # Required for HA 2022.7
        self.coordinator_context = object()

    @property
    def unique_id(self) -> str:
        return f'{self._dog_id}-{self.description.key}'

    @property
    def description(self) -> PitPatSensorEntityDescription:
        return self.entity_description

    @property
    def data(self):
        return self.coordinator.dogs.get(self._dog_id)

    @property
    def native_value(self):
        try:
            return self.description.value_fn(self.data)
        except Exception as e:
            raise ValueError(f"Unable to get value for {self.entity_description.key} sensor entity for dog id {self._dog_id}") from e

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
            ATTR_NAME: self.data.get('Name'),
            ATTR_MANUFACTURER: MANUFACTURER,
            ATTR_SW_VERSION: self.data.get("Monitor", {}).get("FirmwareVersion", ""),
            ATTR_HW_VERSION: self.data.get("Monitor", {}).get("HardwareVersion", ""),
            ATTR_SERIAL_NUMBER: _get_monitor(self.data).get('SerialNumber')
        }

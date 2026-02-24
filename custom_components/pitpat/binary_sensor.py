from dataclasses import dataclass
import logging
from typing import Any, Callable, Dict

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_NAME,
    ATTR_MANUFACTURER,
    ATTR_SW_VERSION,
    ATTR_HW_VERSION,
    ATTR_SERIAL_NUMBER,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
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

@dataclass(frozen=True, kw_only=True)
class PitPatBinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict], str | int | float | None]
    attributes_fn: Callable[[dict], dict | None] = None

DOG_ENTITY_DESCRIPTIONS = [
    PitPatBinarySensorEntityDescription(
        key="live_tracking_active",
        translation_key="live_tracking_active",
        value_fn=lambda data: _get_monitor(data).get('LiveTrackingReason', 0) != 0,
    ),
    PitPatBinarySensorEntityDescription(
        key="charging_status",
        translation_key="charging_status",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda data: bool(_get_monitor(data).get('BatteryInfo', {}).get('Value', {}).get('IsCharging', False)),
    ),
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add the Entities from the config."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    sensors = []

    for dog_id in coordinator.dogs.keys():
        for description in DOG_ENTITY_DESCRIPTIONS:
            sensors.append(PitPatDogBinarySensorEntity(coordinator, dog_id, description))

    async_add_entities(sensors, True)

class PitPatDogBinarySensorEntity(CoordinatorEntity[PitPatDataUpdateCoordinator], BinarySensorEntity):

    _attr_has_entity_name = True # Required for reading translation_key from EntityDescription

    def __init__(self, coordinator: PitPatDataUpdateCoordinator, dog_id: str, description: PitPatBinarySensorEntityDescription):
        CoordinatorEntity.__init__(self, coordinator)
        self._dog_id = dog_id
        self.entity_description = description

        # Required for HA 2022.7
        self.coordinator_context = object()

    @property
    def unique_id(self) -> str:
        return f'{self._dog_id}-{self.description.key}'

    @property
    def description(self) -> PitPatBinarySensorEntityDescription:
        return self.entity_description

    @property
    def data(self):
        return self.coordinator.dogs.get(self._dog_id)

    @property
    def is_on(self):
        try:
            return self.description.value_fn(self.data)
        except Exception as e:
            raise ValueError(f"Unable to get value for {self.entity_description.key} binary sensor entity for dog id {self._dog_id}") from e

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

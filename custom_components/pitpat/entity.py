from typing import Any, Dict

from homeassistant.const import ATTR_HW_VERSION, ATTR_IDENTIFIERS, ATTR_MANUFACTURER, ATTR_MODEL, ATTR_MODEL_ID, ATTR_NAME, ATTR_SERIAL_NUMBER, ATTR_SW_VERSION
from homeassistant.core import DOMAIN
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_MODEL_MAP, MANUFACTURER
from .coordinator import PitPatDataUpdateCoordinator


class PitPatDogEntity(CoordinatorEntity[PitPatDataUpdateCoordinator]):

    _attr_has_entity_name = True # Required for reading translation_key from EntityDescription

    def __init__(self, coordinator: PitPatDataUpdateCoordinator, dog_id: str, description: EntityDescription):
        CoordinatorEntity.__init__(self, coordinator)
        self.__dog_id = dog_id
        self.entity_description = description

        self._attr_unique_id = f'{self.dog_id}-{self.entity_description.key}'

        # Required for HA 2022.7
        self.coordinator_context = object()

    @property
    def dog_id(self) -> str:
        return self.__dog_id

    @property
    def data_dog(self) -> dict:
        return self.coordinator.dogs.get(self.dog_id)

    @property
    def data_monitor(self) -> dict:
        return self.data_dog.get('monitor_details', {}).get('Value', {}).get('Monitor', {})

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        return {
            "dog_id": self.dog_id,
        }

    @property
    def device_info(self):
        """Return device information about this device."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self.dog_id)},
            ATTR_NAME: self.data_dog.get('Name'),
            ATTR_MANUFACTURER: MANUFACTURER,
            ATTR_MODEL_ID: self.data_dog.get('Monitor', {}).get('Model'),
            ATTR_MODEL: DEVICE_MODEL_MAP.get(int(self.data_dog.get('Monitor', {}).get('Model')), ''),
            ATTR_SW_VERSION: self.data_dog.get("Monitor", {}).get("FirmwareVersion", ""),
            ATTR_HW_VERSION: self.data_dog.get("Monitor", {}).get("HardwareVersion", ""),
            ATTR_SERIAL_NUMBER: self.data_monitor.get('SerialNumber')
        }

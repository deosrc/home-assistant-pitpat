from typing import Any, Dict, Generic, TypeVar

from homeassistant.const import (
    ATTR_HW_VERSION,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_MODEL_ID,
    ATTR_NAME,
    ATTR_SERIAL_NUMBER,
    ATTR_SW_VERSION,
)
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEVICE_MODEL_MAP,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import PitPatDataUpdateCoordinator
from .models import PitPatDogData

TDescription = TypeVar('TDescription', bound=EntityDescription)

class PitPatDogEntity(CoordinatorEntity[PitPatDataUpdateCoordinator], Generic[TDescription]):

    entity_description: TDescription
    _attr_has_entity_name = True # Required for reading translation_key from EntityDescription

    def __init__(self, coordinator: PitPatDataUpdateCoordinator, dog_id: str, description: TDescription):
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
    def data(self) -> PitPatDogData | None:
        return self.coordinator.data.get(self.dog_id)

    @property
    def data_dog(self) -> dict:
        return self.data.raw_dog_data

    @property
    def data_monitor(self) -> dict:
        if self.data.raw_monitor_data:
            return self.data.raw_monitor_data

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
            ATTR_NAME: self.data.name,
            ATTR_MANUFACTURER: MANUFACTURER,
            ATTR_MODEL_ID: self.data.device_details.model_id,
            ATTR_MODEL: DEVICE_MODEL_MAP.get(self.data.device_details.model_id),
            ATTR_SW_VERSION: self.data.device_details.firmware_version,
            ATTR_HW_VERSION: self.data.device_details.hardware_version,
            ATTR_SERIAL_NUMBER: self.data.device_details.serial_number
        }

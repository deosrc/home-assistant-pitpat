
from datetime import timedelta
import logging
from typing import Dict
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator
)

from .api import PitPatApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PitPatDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """DataUpdateCoordinator to handle fetching data from PitPat."""

    dogs: Dict[str, dict]

    def __init__(self, hass: HomeAssistant, update_interval, config_data):
        """Initialize the coordinator and set up the Controller object."""
        self._hass = hass

        self.api_client = PitPatApiClient.from_config(hass, config_data)
        self._available = True

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval),
        )

    async def _async_update_data(self):
        """Fetch data"""
        dogs = await self.api_client.async_get_dogs()
        self.dogs = { d['Id']: d for d in dogs}

        for dog_id in self.dogs.keys():
            self.dogs[dog_id] = await self._async_update_dog_data(dog_id)

    async def _async_update_dog_data(self, dog_id):
        base_details = self.dogs[dog_id]

        monitor_details = await self.api_client.async_get_monitor(dog_id)
        all_activity_days = await self.api_client.async_get_all_activity_days(dog_id)

        activity_today = None
        if (len(all_activity_days) > 0):
            activity_today = sorted(all_activity_days, key=lambda item: item.get('Date'), reverse=True)[0]

        return {
            **base_details,
            **{
                'monitor_details': monitor_details,
                'activity_today': activity_today,
            }
        }

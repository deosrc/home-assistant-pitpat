
from datetime import timedelta
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator
)

from .api import PitPatApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PitPatDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """DataUpdateCoordinator to handle fetching data from PitPat."""

    def __init__(self, hass: HomeAssistant, update_interval, config_data):
        """Initialize the coordinator and set up the Controller object."""
        self._hass = hass

        self._api_client = PitPatApiClient.from_config(hass, config_data)
        self._available = True

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval),
        )

    async def _async_update_data(self):
        """Fetch data"""
        pass


from datetime import timedelta
import logging
from typing import Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator
)

from .api import InvalidCredentialsError, PitPatApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PitPatDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """DataUpdateCoordinator to handle fetching data from PitPat."""

    dogs: Dict[str, dict]

    def __init__(self, hass: HomeAssistant, update_interval, config_entry: ConfigEntry):
        """Initialize the coordinator and set up the Controller object."""
        self._hass = hass
        self._config_entry = config_entry

        self._available = True
        self.api_client: PitPatApiClient | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval),
        )

    async def _async_ensure_ready(self):
        if not self.api_client:
            await self._async_refresh_auth()

        is_authenticated = await self.api_client.async_ensure_user_id_present()
        if not is_authenticated:
            raise ConfigEntryAuthFailed()

    async def _async_refresh_auth(self):
        _LOGGER.info('Preparing new API client from refresh token.')
        try:
            session = async_create_clientsession(self._hass)
            tokens = await PitPatApiClient.async_authenticate_from_refresh_token(session, self._config_entry.data.get('refresh_token'))
            self.api_client = PitPatApiClient(session, tokens)
        except InvalidCredentialsError as err:
            raise ConfigEntryAuthFailed() from err

    async def _async_update_data(self):
        """Fetch data"""
        try:
            await self._async_refresh_data()
        except Exception as err:
            _LOGGER.warning('Request failed. Attempting to re-authenticate.', exc_info=err)
            self.api_client = None
            await self._async_refresh_data()

    async def _async_refresh_data(self) -> None:
        await self._async_ensure_ready()

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

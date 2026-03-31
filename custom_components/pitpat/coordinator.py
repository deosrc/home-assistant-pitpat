
from datetime import timedelta
import logging
from typing import Any, Dict, Tuple

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator
)

from .api import InvalidCredentialsError, PitPatApiClient
from .const import DOMAIN
from .models import PitPatDogData, map_dog_data

_LOGGER = logging.getLogger(__name__)

TCoordinatorData = Dict[str, dict]

class PitPatDataUpdateCoordinator(DataUpdateCoordinator[TCoordinatorData]):
    """DataUpdateCoordinator to handle fetching data from PitPat."""

    def __init__(self, hass: HomeAssistant, update_interval: int, config_entry: ConfigEntry):
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

    async def _async_update_data(self) -> TCoordinatorData:
        """Fetch data"""
        try:
            return await self._async_refresh_data()
        except ConfigEntryAuthFailed as err:
            _LOGGER.info('API client is not authenticated. Attempting to re-authenticate.', exc_info=err)
            self.api_client = None
            return await self._async_refresh_data()
        except Exception as err:
            _LOGGER.warning('Request failed. Retrying with new API client.', exc_info=err)
            self.api_client = None
            return await self._async_refresh_data()

    async def _async_refresh_data(self) -> TCoordinatorData:
        await self._async_ensure_ready()

        dogs = await self.api_client.async_get_dogs()

        data = {}
        for d in dogs:
            dog_id, dog_data = await self._async_get_dog_data(d)
            data[dog_id] = dog_data

        return data

    async def _async_get_dog_data(self, initial_data: Dict[str, Any]) -> Tuple[str, PitPatDogData]:
        dog_id: str = initial_data['Id']

        monitor_data = await self.api_client.async_get_monitor(dog_id)
        all_activity_days = await self.api_client.async_get_all_activity_days(dog_id)

        return dog_id, map_dog_data(initial_data, monitor_data, all_activity_days)

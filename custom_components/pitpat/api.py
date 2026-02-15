from typing import Any, Dict, List
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import CONFIG_KEY_TOKEN

class MissingUserIdError(Exception):
    pass

class PitPatApiClient():

    @staticmethod
    def from_config(hass: HomeAssistant, config: Dict[str, Any]):
        token = config[CONFIG_KEY_TOKEN]
        session = async_create_clientsession(hass)
        api_client = PitPatApiClient(session, token)
        return api_client

    def __init__(self, session: aiohttp.ClientSession, token: str):
        self._session = session
        self._token = token

        self.__user_id: str | None = None

    async def async_get_user_id(self) -> str:
        if not self.__user_id:
            settings = await self.async_get_settings()
            self.__user_id = settings.get('UserId')

        if not self.__user_id:
            raise MissingUserIdError()

        return self.__user_id

    async def async_get_settings(self) -> Dict[str, str]:
        result = await self._session.get(
            'https://api.pitpat.com/api/Settings',
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()
        return await result.json()

    async def async_get_dogs(self) -> List[Any]:
        user_id = await self.async_get_user_id()
        result = await self._session.get(
            f"https://api.pitpat.com/api/Users/{user_id}/Dogs",
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()
        return await result.json()

    async def async_get_monitor(self, dog_id) -> Dict[str, dict]:
        user_id = await self.async_get_user_id()
        result = await self._session.get(
            f"https://api.pitpat.com/api/Users/{user_id}/Dogs/{dog_id}/Monitors",
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()
        return await result.json()

    async def async_get_all_activity_days(self, dog_id) -> Dict[str, dict]:
        user_id = await self.async_get_user_id()
        result = await self._session.get(
            f'https://activity.pitpat.com/api/Users/{user_id}/Dogs/{dog_id}/AllActivityDays',
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()
        return await result.json()

    async def async_tracking_stop(self, dog_id) -> None:
        user_id = await self.async_get_user_id()
        result = await self._session.put(
            f'https://location.pitpat.com/api/user/{user_id}/dog/{dog_id}/livetracking/stop',
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()

    async def async_tracking_start_find(self, dog_id) -> None:
        user_id = await self.async_get_user_id()
        result = await self._session.put(
            f'https://location.pitpat.com/api/user/{user_id}/dog/{dog_id}/livetracking/start/find',
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()

    async def async_tracking_start_walk(self, dog_id) -> None:
        user_id = await self.async_get_user_id()
        result = await self._session.put(
            f'https://location.pitpat.com/api/user/{user_id}/dog/{dog_id}/livetracking/start/walk',
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()

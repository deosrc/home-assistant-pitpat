from typing import Any, Dict, List
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import CONFIG_KEY_TOKEN, CONFIG_KEY_USER_ID

class PitPatApiClient():

    @staticmethod
    def from_config(hass: HomeAssistant, config: Dict[str, Any]):
        token = config[CONFIG_KEY_TOKEN]
        user_id = config[CONFIG_KEY_USER_ID]
        session = async_create_clientsession(hass)
        api_client = PitPatApiClient(session, token, user_id)
        return api_client

    def __init__(self, session: aiohttp.ClientSession, token: str, user_id : str):
        self._session = session
        self._token = token
        self._user_id = user_id

    async def async_get_dogs(self) -> List[Any]:
        result = await self._session.get(
            f"https://api.pitpat.com/api/Users/{self._user_id}/Dogs",
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()
        return await result.json()

    async def async_get_monitor(self, dog_id) -> Dict[str, dict]:
        result = await self._session.get(
            f"https://api.pitpat.com/api/Users/{self._user_id}/Dogs/{dog_id}/Monitors",
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()
        return await result.json()

    async def async_get_all_activity_days(self, dog_id) -> Dict[str, dict]:
        result = await self._session.get(
            f'https://activity.pitpat.com/api/Users/{self._user_id}/Dogs/{dog_id}/AllActivityDays',
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()
        return await result.json()

    async def async_tracking_stop(self, dog_id) -> None:
        result = await self._session.put(
            f'https://location.pitpat.com/api/user/{self._user_id}/dog/{dog_id}/livetracking/stop',
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()

    async def async_tracking_start_find(self, dog_id) -> None:
        result = await self._session.put(
            f'https://location.pitpat.com/api/user/{self._user_id}/dog/{dog_id}/livetracking/start/find',
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()

    async def async_tracking_start_walk(self, dog_id) -> None:
        result = await self._session.put(
            f'https://location.pitpat.com/api/user/{self._user_id}/dog/{dog_id}/livetracking/start/walk',
            headers = {
                'Authorization': f'Bearer {self._token}'
            })
        result.raise_for_status()

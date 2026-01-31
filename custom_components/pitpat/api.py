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

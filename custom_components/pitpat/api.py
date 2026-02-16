from typing import Any, Dict, List
import aiohttp

class InvalidCredentialsError(Exception):
    pass

class PitPatApiClient():

    __HOST_AUTH = 'https://auth.pitpat.com'
    __HOST_API = 'https://api.pitpat.com'
    __HOST_ACTIVITY = 'https://activity.pitpat.com'
    __HOST_LOCATION = 'https://location.pitpat.com'

    @staticmethod
    async def async_authenticate_from_credentials(session: aiohttp.ClientSession, username: str, password: str) -> Dict[str, Any]:
        return await PitPatApiClient.__async_authenticate(
            session,
            {
                'grant_type': 'password',
                'username': username,
                'password': password,
            }
        )

    @staticmethod
    async def async_authenticate_from_refresh_token(session: aiohttp.ClientSession, refresh_token: str) -> Dict[str, Any]:
        return await PitPatApiClient.__async_authenticate(
            session,
            {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            }
        )

    @staticmethod
    async def __async_authenticate(session: aiohttp.ClientSession, data: Dict[str, str]) -> Dict[str, Any]:
        form_data = aiohttp.FormData()
        form_data.add_field('client_id', 'PitPatApp')
        form_data.add_field('scope', 'PitPatApi offline_access')
        for key, val in data.items():
            form_data.add_field(key, val)

        result = await session.post(
            f'{PitPatApiClient.__HOST_AUTH}/connect/token',
            data=form_data)

        response: Dict[str, Any] = await result.json()
        if result.status == 400 and 'invalid_grant' == response.get('error'):
            raise InvalidCredentialsError()

        result.raise_for_status()
        return response

    def __init__(self, session: aiohttp.ClientSession, tokens: Dict[str, Any]):
        self._session = session
        self._tokens = tokens

        self.__user_id: str | None = None

    @property
    def default_headers(self):
        return {
            'Authorization': f'{self._tokens.get('token_type')} {self._tokens.get('access_token')}'
        }

    async def async_get_settings(self) -> Dict[str, str]:
        result = await self._session.get(
            f'{PitPatApiClient.__HOST_API}/api/Settings',
            headers=self.default_headers)
        result.raise_for_status()
        return await result.json()

    async def async_get_dogs(self) -> List[Any]:
        await self.async_ensure_user_id_present()
        result = await self._session.get(
            f'{PitPatApiClient.__HOST_API}/api/Users/{self.__user_id}/Dogs',
            headers=self.default_headers)
        result.raise_for_status()
        return await result.json()

    async def async_get_monitor(self, dog_id) -> Dict[str, dict]:
        await self.async_ensure_user_id_present()
        result = await self._session.get(
            f'{PitPatApiClient.__HOST_API}/api/Users/{self.__user_id}/Dogs/{dog_id}/Monitors',
            headers=self.default_headers)
        result.raise_for_status()
        return await result.json()

    async def async_get_all_activity_days(self, dog_id) -> Dict[str, dict]:
        await self.async_ensure_user_id_present()
        result = await self._session.get(
            f'{PitPatApiClient.__HOST_ACTIVITY}/api/Users/{self.__user_id}/Dogs/{dog_id}/AllActivityDays',
            headers=self.default_headers)
        result.raise_for_status()
        return await result.json()

    async def async_tracking_stop(self, dog_id) -> None:
        await self.async_ensure_user_id_present()
        result = await self._session.put(
            f'{PitPatApiClient.__HOST_LOCATION}/api/user/{self.__user_id}/dog/{dog_id}/livetracking/stop',
            headers=self.default_headers)
        result.raise_for_status()

    async def async_tracking_start_find(self, dog_id) -> None:
        await self.async_ensure_user_id_present()
        result = await self._session.put(
            f'{PitPatApiClient.__HOST_LOCATION}/api/user/{self.__user_id}/dog/{dog_id}/livetracking/start/find',
            headers=self.default_headers)
        result.raise_for_status()

    async def async_tracking_start_walk(self, dog_id) -> None:
        await self.async_ensure_user_id_present()
        result = await self._session.put(
            f'{PitPatApiClient.__HOST_LOCATION}/api/user/{self.__user_id}/dog/{dog_id}/livetracking/start/walk',
            headers=self.default_headers)
        result.raise_for_status()

    async def async_ensure_user_id_present(self) -> bool:
        if self.__user_id:
            return

        settings = await self.async_get_settings()
        self.__user_id = settings.get('UserId')
        return bool(self.__user_id)

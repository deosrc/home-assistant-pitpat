import logging
from typing import Any, Dict, List
import aiohttp

_LOGGER = logging.getLogger(__name__)

class InvalidCredentialsError(Exception):
    """The operation failed due to invalid or expired credentials."""
    pass

class PitPatApiClient():
    """API Client for PitPat pet trackers."""

    __HOST_AUTH = 'https://auth.pitpat.com'
    __HOST_API = 'https://api.pitpat.com'
    __HOST_ACTIVITY = 'https://activity.pitpat.com'
    __HOST_LOCATION = 'https://location.pitpat.com'

    @staticmethod
    async def async_authenticate_from_credentials(session: aiohttp.ClientSession, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with PitPat using username and password.

        :param session: aiohttp session to use for the request
        :type session: aiohttp.ClientSession
        :param username: Username for the account
        :type username: str
        :param password: Password for the account
        :type password: str
        :return: The response of the auth request
        :rtype: Dict[str, Any]
        """
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
        """
        Refresh the auth token.

        :param session: aiohttp session to use for the request
        :type session: aiohttp.ClientSession
        :param refresh_token: The refresh token for the session
        :type refresh_token: str
        :return: The response of the auth request
        :rtype: Dict[str, Any]
        """
        return await PitPatApiClient.__async_authenticate(
            session,
            {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            }
        )

    @staticmethod
    async def __async_authenticate(session: aiohttp.ClientSession, data: Dict[str, str]) -> Dict[str, Any]:
        """
        Send an authentication request.

        :param session: aiohttp session to use for the request
        :type session: aiohttp.ClientSession
        :param data: Data to use for the authentication request.
        :type data: str
        :return: The response of the auth request
        :rtype: Dict[str, Any]
        """
        _LOGGER.info('Authenticating using grant type %s', data.get('grant_type'))

        form_data = aiohttp.FormData()
        form_data.add_field('client_id', 'PitPatApp')
        form_data.add_field('scope', 'PitPatApi offline_access')
        for key, val in data.items():
            form_data.add_field(key, val)

        result = await session.post(
            f'{PitPatApiClient.__HOST_AUTH}/connect/token',
            data=form_data)
        _LOGGER.info('Received %i status code from auth request', result.status)

        response: Dict[str, Any] = await result.json()
        _LOGGER.debug('Auth response: %s', response)

        if result.status == 400 and 'invalid_grant' == response.get('error'):
            _LOGGER.warning('Auth request failed: %s', response)
            raise InvalidCredentialsError()

        result.raise_for_status()
        return response

    def __init__(self, session: aiohttp.ClientSession, tokens: Dict[str, Any]):
        self._session = session
        self._tokens = tokens

        self.__user_id: str | None = None

    @property
    def default_headers(self):
        """
        The default headers to use for requests.
        """
        return {
            'Authorization': f'{self._tokens.get('token_type')} {self._tokens.get('access_token')}'
        }

    async def async_get_settings(self) -> Dict[str, str]:
        """
        Retrieves account settings.

        :return: Account settings.
        :rtype: Dict[str, str]
        """
        _LOGGER.debug('Retrieving account settings')

        result = await self._session.get(
            f'{PitPatApiClient.__HOST_API}/api/Settings',
            headers=self.default_headers)

        result.raise_for_status()
        return await result.json()

    async def async_get_dogs(self) -> List[Any]:
        """
        Retrieve information for degs registered to the account.

        :return: Details of dogs registered to the account.
        :rtype: List[Any]
        """
        _LOGGER.debug('Retrieving dog information')

        await self.async_ensure_user_id_present()
        result = await self._session.get(
            f'{PitPatApiClient.__HOST_API}/api/Users/{self.__user_id}/Dogs',
            headers=self.default_headers)

        result.raise_for_status()
        return await result.json()

    async def async_get_monitor(self, dog_id) -> Dict[str, dict]:
        """
        Retrieve information for a monitor registered to the account.

        :param dog_id: The Id for the dog the monitor is registered to.
        :return: Details of the monitor.
        :rtype: Dict[str, dict]
        """
        _LOGGER.debug('Retrieving monitor information')

        await self.async_ensure_user_id_present()
        result = await self._session.get(
            f'{PitPatApiClient.__HOST_API}/api/Users/{self.__user_id}/Dogs/{dog_id}/Monitors',
            headers=self.default_headers)

        result.raise_for_status()
        return await result.json()

    async def async_get_all_activity_days(self, dog_id) -> List[Dict[str, dict]]:
        """
        Retrieve information for activity by day.

        :param dog_id: The Id for the dog the monitor is registered to.
        :return: A list of activity by day.
        :rtype: List[Dict[str, dict]]
        """
        _LOGGER.debug('Retrieving activity days')

        await self.async_ensure_user_id_present()
        result = await self._session.get(
            f'{PitPatApiClient.__HOST_ACTIVITY}/api/Users/{self.__user_id}/Dogs/{dog_id}/AllActivityDays',
            headers=self.default_headers)

        result.raise_for_status()
        return await result.json()

    async def async_tracking_stop(self, dog_id) -> None:
        """
        Stops active tracking.

        :param dog_id: The Id for the dog the monitor is registered to.
        """
        await self.async_ensure_user_id_present()
        result = await self._session.put(
            f'{PitPatApiClient.__HOST_LOCATION}/api/user/{self.__user_id}/dog/{dog_id}/livetracking/stop',
            headers=self.default_headers)

        result.raise_for_status()

    async def async_tracking_start_find(self, dog_id) -> None:
        """
        Starts active tracking in "find my dog" mode.

        :param dog_id: The Id for the dog the monitor is registered to.
        """
        _LOGGER.debug('Starting "find my dog" tracking')

        await self.async_ensure_user_id_present()
        result = await self._session.put(
            f'{PitPatApiClient.__HOST_LOCATION}/api/user/{self.__user_id}/dog/{dog_id}/livetracking/start/find',
            headers=self.default_headers)

        result.raise_for_status()

    async def async_tracking_start_walk(self, dog_id) -> None:
        """
        Starts active tracking in walk mode.

        :param dog_id: The Id for the dog the monitor is registered to.
        """
        _LOGGER.debug('Starting walk tracking')

        await self.async_ensure_user_id_present()
        result = await self._session.put(
            f'{PitPatApiClient.__HOST_LOCATION}/api/user/{self.__user_id}/dog/{dog_id}/livetracking/start/walk',
            headers=self.default_headers)

        result.raise_for_status()

    async def async_ensure_user_id_present(self) -> bool:
        """
        Ensures the current user Id is configured on the API client.

        :return: True if the user Id is available (i.e. the client is authenticated), otherwise false.
        :rtype: bool
        """
        if self.__user_id:
            _LOGGER.debug('User Id is already known as %s', self.__user_id)
            return

        settings = await self.async_get_settings()
        self.__user_id = settings.get('UserId')
        _LOGGER.info('User Id detected as %s', self.__user_id)
        return bool(self.__user_id)

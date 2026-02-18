"""Config flow for PitPat integration."""
import logging
from typing import Any, Dict, Mapping

from aiohttp import ClientResponseError
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    ConfigEntry,
    CONN_CLASS_CLOUD_POLL,
    SOURCE_REAUTH,
)
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.core import (
    callback,
    HomeAssistant
)
from requests.exceptions import ConnectionError

from .api import InvalidCredentialsError, PitPatApiClient
from .const import (
    DOMAIN,
)
from .options_flow import OptionsFlowHandler

_LOGGER = logging.getLogger(__name__)

DATA_KEY_EMAIL = 'email'
DATA_KEY_PASSWORD = 'password'

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(DATA_KEY_EMAIL): str,
        vol.Required(DATA_KEY_PASSWORD): str,
    }
)

async def validate_input(hass: HomeAssistant, username: str, password: str) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    session = async_create_clientsession(hass)
    return await PitPatApiClient.async_authenticate_from_credentials(session, username, password)

class PitPatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tdarr Controller."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                username = user_input[DATA_KEY_EMAIL]
                tokens = await validate_input(self.hass, username, user_input[DATA_KEY_PASSWORD])
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(),
                        data_updates=tokens,
                        reload_even_if_entry_is_unchanged=True
                    )
                else:
                    return self.async_create_entry(
                        title=username,
                        data=tokens)
            except ConnectionError as err:
                _LOGGER.exception(err)
                errors["base"] = "cannot_connect"
            except InvalidCredentialsError as err:
                _LOGGER.exception(err)
                errors['base'] = 'invalid_auth'
            except ClientResponseError as err:
                _LOGGER.exception(err)
                errors["base"] = "unknown"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception(ex)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

"""Config flow for PitPat integration."""
import logging
from typing import Any, Dict

from aiohttp import ClientResponseError
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigEntry,
    CONN_CLASS_CLOUD_POLL
)
from homeassistant.core import (
    callback,
    HomeAssistant
)
from requests.exceptions import ConnectionError

from .api import InvalidCredentialsError, PitPatApiClient
from .const import (
    DOMAIN,
    CONFIG_KEY_REFRESH_TOKEN,
)
from .options_flow import OptionsFlowHandler

_LOGGER = logging.getLogger(__name__)

DATA_KEY_USERNAME = 'username'
DATA_KEY_PASSWORD = 'password'

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(DATA_KEY_USERNAME): str,
        vol.Required(DATA_KEY_PASSWORD): str,
    }
)

async def validate_input(hass: HomeAssistant, username: str, password: str) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    refresh_token = await PitPatApiClient.async_get_refresh_token(hass, username, password)
    return refresh_token

class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tdarr Controller."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                refresh_token = await validate_input(self.hass, user_input[DATA_KEY_USERNAME], user_input[DATA_KEY_PASSWORD])
                return self.async_create_entry(
                    title="PitPat",
                    data={
                        CONFIG_KEY_REFRESH_TOKEN: refresh_token
                    })
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

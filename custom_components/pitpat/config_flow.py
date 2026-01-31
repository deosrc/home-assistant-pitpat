"""Config flow for PitPat integration."""
import logging

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
from homeassistant.exceptions import HomeAssistantError
from requests.exceptions import ConnectionError

from .api import PitPatApiClient
from .const import (
    DOMAIN,
    CONFIG_KEY_TOKEN,
    CONFIG_KEY_USER_ID
)
from .options_flow import OptionsFlowHandler

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONFIG_KEY_TOKEN): str,
        vol.Required(CONFIG_KEY_USER_ID): str,
    }
)

async def validate_input(hass: HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    api_client: PitPatApiClient = PitPatApiClient.from_config(hass, data)

    try:
        await api_client.async_get_dogs()
    except:
        _LOGGER.error("Failed to connect to PitPat")
        raise HomeAssistantError()

class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tdarr Controller."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
                return self.async_create_entry(title="PitPat", data=user_input)
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except ClientResponseError as err:
                _LOGGER.exception(err)
                if (err.code == 401):
                    errors["base"] = "invalid_auth"
                else:
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

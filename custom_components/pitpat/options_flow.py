"""Options flow for PitPat integration."""

import logging
import voluptuous as vol
from homeassistant.config_entries import (
    OptionsFlow,
)
from homeassistant.exceptions import HomeAssistantError

from .const import (
    UPDATE_INTERVAL,
    UPDATE_INTERVAL_DEFAULT,
)

_LOGGER = logging.getLogger(__name__)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(UPDATE_INTERVAL, default=UPDATE_INTERVAL_DEFAULT): int,
    }
)

class OptionsFlowHandler(OptionsFlow):

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            _LOGGER.debug(user_input)
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ))

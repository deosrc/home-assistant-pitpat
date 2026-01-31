"""PitPat custom integration for Home Assistant."""

import asyncio
import logging
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.config_entries import ConfigEntry

from .coordinator import PitPatDataUpdateCoordinator
from .const import DOMAIN

PLATFORMS = []

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Tdarr component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def options_update_listener(hass: HomeAssistant,  entry: ConfigEntry):
    _LOGGER.info("Options updated")
    await hass.config_entries.async_reload(entry.entry_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Tdarr Server from a config entry."""
    # TODO: Load update interval from options
    coordinator = PitPatDataUpdateCoordinator(hass, 5, entry.data)

    # Get initial data so that correct sensors can be created
    await coordinator.async_refresh()

    # Registers update listener to update config entry when options are updated.
    entry.add_update_listener(options_update_listener)

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

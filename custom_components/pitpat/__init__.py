"""PitPat custom integration for Home Assistant."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.config_entries import ConfigEntry

from .coordinator import PitPatDataUpdateCoordinator
from .const import (
    COORDINATOR,
    DOMAIN,
    UPDATE_INTERVAL,
    UPDATE_INTERVAL_DEFAULT,
)

PLATFORMS = []

_LOGGER = logging.getLogger(__name__)

def _get_update_interval(config_entry: ConfigEntry):
    return config_entry.options.get(UPDATE_INTERVAL, UPDATE_INTERVAL_DEFAULT)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Tdarr component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Tdarr Server from a config entry."""
    coordinator = PitPatDataUpdateCoordinator(hass, _get_update_interval(entry), entry.data)

    # Get initial data so that correct sensors can be created
    await coordinator.async_refresh()

    # Registers update listener to update config entry when options are updated.
    entry.async_on_unload(entry.add_update_listener(update_listener))

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    coordinator.update_interval = _get_update_interval(config_entry)
    _LOGGER.info("Coordinator settings updated")

"""PitPat custom integration for Home Assistant."""

import asyncio
import logging
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.config_entries import ConfigEntry

from .coordinator import PitPatDataUpdateCoordinator
from .const import (
    DATA_KEY_COORDINATOR,
    DOMAIN,
    OPTIONS_KEY_UPDATE_INTERVAL,
    UPDATE_INTERVAL_DEFAULT,
)

PLATFORMS = [
    "binary_sensor",
    "button",
    "device_tracker",
    "select",
    "sensor",
]

_LOGGER = logging.getLogger(__name__)

def _get_update_interval(config_entry: ConfigEntry):
    return config_entry.options.get(OPTIONS_KEY_UPDATE_INTERVAL, UPDATE_INTERVAL_DEFAULT)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Tdarr component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Tdarr Server from a config entry."""
    coordinator = PitPatDataUpdateCoordinator(hass, _get_update_interval(entry), entry)

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_KEY_COORDINATOR: coordinator,
    }

    # Get initial data so that correct sensors can be created
    await coordinator.async_refresh()

    # Registers update listener to update config entry when options are updated.
    entry.async_on_unload(entry.add_update_listener(update_listener))

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_KEY_COORDINATOR]
    await coordinator.async_shutdown()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    coordinator: PitPatDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    coordinator.update_interval = _get_update_interval(config_entry)
    _LOGGER.info("Coordinator settings updated")

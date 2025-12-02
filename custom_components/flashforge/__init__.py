"""The Flashforge integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import CONF_IP_ADDRESS, Platform
from homeassistant.exceptions import ConfigEntryNotReady

from flashforge import FlashForgeClient

from .const import CONF_CHECK_CODE, CONF_SERIAL_NUMBER, DOMAIN
from .data_update_coordinator import FlashForgeDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS = [
    Platform.SENSOR,
    Platform.CAMERA,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.LIGHT,
    Platform.FAN,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Flashforge from a config entry."""
    printer = FlashForgeClient(
        entry.data[CONF_IP_ADDRESS],
        entry.data.get(CONF_SERIAL_NUMBER, ""),
        entry.data.get(CONF_CHECK_CODE, ""),
    )
    _LOGGER.debug("FlashForge printer setup")
    coordinator = FlashForgeDataUpdateCoordinator(hass, printer, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except (TimeoutError, ConnectionError) as err:
        _LOGGER.debug("Printer not responding: %s", err)
        raise ConfigEntryNotReady(err) from err
    # Save the coordinator object to be able to access it later on.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

"""Platform for light integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.light import LightEntity
from homeassistant.components.light.const import ColorMode
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .data_update_coordinator import FlashForgeDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Flashforge Light platform."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([FlashForgeLightEntity(coordinator)])


class FlashForgeLightEntity(
    CoordinatorEntity[FlashForgeDataUpdateCoordinator], LightEntity
):
    """An entity using CoordinatorEntity."""

    _attr_has_entity_name = True
    _attr_translation_key = "light"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self._device_id = coordinator.config_entry.unique_id
        self._attr_device_info = coordinator.device_info
        self._attr_name = "Light"
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_light"

        self.supported_color_modes = {ColorMode.ONOFF}
        self.color_mode = ColorMode.ONOFF

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        endstop_status = self.coordinator.data.get("endstop_status")
        if endstop_status:
            self._attr_is_on = endstop_status.led_enabled
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn the light on."""
        await self.coordinator.client.tcp_client.led_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the light off."""
        await self.coordinator.client.tcp_client.led_off()
        await self.coordinator.async_request_refresh()

"""Switch platform for FlashForge printer on/off controls."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback

from . import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data_update_coordinator import FlashForgeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlashForge switch entities."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities: list[SwitchEntity] = [
        FlashForgeLEDSwitch(coordinator),
        FlashForgeRunoutSensorSwitch(coordinator),
    ]

    # Add camera switch only for Pro models
    if coordinator.client.is_pro:
        entities.append(FlashForgeCameraSwitch(coordinator))

    # Add filtration switch only if equipped
    if coordinator.client.filtration_control:
        entities.append(FlashForgeFiltrationSwitch(coordinator))

    async_add_entities(entities)


class FlashForgeLEDSwitch(SwitchEntity):
    """Representation of LED light switch."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:lightbulb"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the LED switch."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_led_switch"
        self._attr_name = "LED Lights"
        self._attr_device_info = coordinator.device_info
        self._attr_is_on = False

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on LED lights."""
        try:
            await self.coordinator.client.control.set_led_on()
            self._attr_is_on = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error turning on LED lights")

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off LED lights."""
        try:
            await self.coordinator.client.control.set_led_off()
            self._attr_is_on = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error turning off LED lights")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.client.led_control
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update state from coordinator if available
        self.async_write_ha_state()


class FlashForgeCameraSwitch(SwitchEntity):
    """Representation of camera on/off switch for Pro models."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:camera"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the camera switch."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_camera_switch"
        self._attr_name = "Camera"
        self._attr_device_info = coordinator.device_info
        self._attr_is_on = False

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on camera."""
        try:
            await self.coordinator.client.control.turn_camera_on()
            self._attr_is_on = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error turning on camera")

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off camera."""
        try:
            await self.coordinator.client.control.turn_camera_off()
            self._attr_is_on = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error turning off camera")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.client.is_pro

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class FlashForgeRunoutSensorSwitch(SwitchEntity):
    """Representation of filament runout sensor switch."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:printer-3d-nozzle-alert"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the runout sensor switch."""
        self.coordinator = coordinator
        self._attr_unique_id = (
            f"{coordinator.config_entry.unique_id}_runout_sensor_switch"
        )
        self._attr_name = "Filament Runout Sensor"
        self._attr_device_info = coordinator.device_info
        self._attr_is_on = True  # Assume on by default

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on runout sensor."""
        try:
            await self.coordinator.client.control.turn_runout_sensor_on()
            self._attr_is_on = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error turning on runout sensor")

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off runout sensor."""
        try:
            await self.coordinator.client.control.turn_runout_sensor_off()
            self._attr_is_on = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error turning off runout sensor")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class FlashForgeFiltrationSwitch(SwitchEntity):
    """Representation of filtration system switch."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the filtration switch."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_filtration_switch"
        self._attr_name = "Filtration System"
        self._attr_device_info = coordinator.device_info
        self._attr_is_on = False
        self._filtration_mode = "off"  # off, internal, external

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on filtration (defaults to external)."""
        try:
            await self.coordinator.client.control.set_external_filtration_on()
            self._attr_is_on = True
            self._filtration_mode = "external"
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error turning on filtration")

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off filtration."""
        try:
            await self.coordinator.client.control.set_filtration_off()
            self._attr_is_on = False
            self._filtration_mode = "off"
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error turning off filtration")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.client.filtration_control
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "filtration_mode": self._filtration_mode,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

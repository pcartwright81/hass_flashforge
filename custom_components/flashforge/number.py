"""Number platform for FlashForge printer numeric controls."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE, UnitOfLength

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
    """Set up FlashForge number entities."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities = [
        FlashForgePrintSpeedNumber(coordinator),
        FlashForgeZOffsetNumber(coordinator),
        FlashForgeChamberFanNumber(coordinator),
        FlashForgeCoolingFanNumber(coordinator),
    ]

    async_add_entities(entities)


class FlashForgePrintSpeedNumber(NumberEntity):
    """Representation of print speed override control."""

    _attr_has_entity_name = True
    _attr_native_min_value = 50
    _attr_native_max_value = 200
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the print speed number entity."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_print_speed"
        self._attr_name = "Print Speed"
        self._attr_device_info = coordinator.device_info
        self._attr_native_value = 100

    async def async_set_native_value(self, value: float) -> None:
        """Set new print speed value."""
        try:
            await self.coordinator.client.control.set_speed_override(int(value))
            self._attr_native_value = value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error setting print speed")

    @property
    def available(self) -> bool:
        """Return True if entity is available and printer is printing."""
        if not self.coordinator.last_update_success:
            return False
        info = self.coordinator.data.get("info")
        if not info or not hasattr(info, "machine_state"):
            return False
        return str(info.machine_state).lower() == "printing"


class FlashForgeZOffsetNumber(NumberEntity):
    """Representation of Z-axis offset override control."""

    _attr_has_entity_name = True
    _attr_native_min_value = -2.0
    _attr_native_max_value = 2.0
    _attr_native_step = 0.05
    _attr_native_unit_of_measurement = UnitOfLength.MILLIMETERS
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:arrow-expand-vertical"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the Z offset number entity."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_z_offset"
        self._attr_name = "Z Axis Offset"
        self._attr_device_info = coordinator.device_info
        self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Set new Z offset value."""
        try:
            await self.coordinator.client.control.set_z_axis_override(value)
            self._attr_native_value = value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error setting Z offset")

    @property
    def available(self) -> bool:
        """Return True if entity is available and printer is printing."""
        if not self.coordinator.last_update_success:
            return False
        info = self.coordinator.data.get("info")
        if not info or not hasattr(info, "machine_state"):
            return False
        return str(info.machine_state).lower() == "printing"


class FlashForgeChamberFanNumber(NumberEntity):
    """Representation of chamber fan speed control."""

    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the chamber fan number entity."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_chamber_fan_speed"
        self._attr_name = "Chamber Fan Speed"
        self._attr_device_info = coordinator.device_info
        self._attr_native_value = 0

    async def async_set_native_value(self, value: float) -> None:
        """Set new chamber fan speed value."""
        try:
            await self.coordinator.client.control.set_chamber_fan_speed(int(value))
            self._attr_native_value = value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error setting chamber fan speed")

    @property
    def available(self) -> bool:
        """Return True if entity is available and printer is printing."""
        if not self.coordinator.last_update_success:
            return False
        info = self.coordinator.data.get("info")
        if not info or not hasattr(info, "machine_state"):
            return False
        return str(info.machine_state).lower() == "printing"


class FlashForgeCoolingFanNumber(NumberEntity):
    """Representation of cooling fan speed control."""

    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the cooling fan number entity."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_cooling_fan_speed"
        self._attr_name = "Cooling Fan Speed"
        self._attr_device_info = coordinator.device_info
        self._attr_native_value = 0

    async def async_set_native_value(self, value: float) -> None:
        """Set new cooling fan speed value."""
        try:
            await self.coordinator.client.control.set_cooling_fan_speed(int(value))
            self._attr_native_value = value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error setting cooling fan speed")

    @property
    def available(self) -> bool:
        """Return True if entity is available and printer is printing."""
        if not self.coordinator.last_update_success:
            return False
        info = self.coordinator.data.get("info")
        if not info or not hasattr(info, "machine_state"):
            return False
        return str(info.machine_state).lower() == "printing"

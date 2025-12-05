"""Climate platform for FlashForge printer temperature control."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

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
    """Set up FlashForge climate entities."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities = [
        FlashForgeBedClimate(coordinator),
        FlashForgeNozzleClimate(coordinator),
    ]

    async_add_entities(entities)


class FlashForgeBedClimate(ClimateEntity):
    """Representation of the heated bed as a climate entity."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes: ClassVar[list[HVACMode]] = [HVACMode.OFF, HVACMode.HEAT]
    _attr_min_temp = 0
    _attr_max_temp = 120

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the bed climate entity."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_bed_climate"
        self._attr_name = "Bed"
        self._attr_device_info = coordinator.device_info

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        info = self.coordinator.data.get("info")
        if info and hasattr(info, "bed_temperature"):
            return float(info.bed_temperature)
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        info = self.coordinator.data.get("info")
        if info and hasattr(info, "target_bed_temperature"):
            return float(info.target_bed_temperature)
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if self.target_temperature and self.target_temperature > 0:
            return HVACMode.HEAT
        return HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        try:
            await self.coordinator.client.temp_control.set_bed_temp(
                int(temperature), wait_for=False
            )
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error setting bed temperature")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        try:
            if hvac_mode == HVACMode.OFF:
                await self.coordinator.client.temp_control.cancel_bed_temp()
            elif hvac_mode == HVACMode.HEAT:
                # Set to a default temperature if turning on
                await self.coordinator.client.temp_control.set_bed_temp(
                    60, wait_for=False
                )
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error setting bed HVAC mode")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success


class FlashForgeNozzleClimate(ClimateEntity):
    """Representation of the nozzle/extruder as a climate entity."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes: ClassVar[list[HVACMode]] = [HVACMode.OFF, HVACMode.HEAT]
    _attr_min_temp = 0
    _attr_max_temp = 300

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the nozzle climate entity."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_nozzle_climate"
        self._attr_name = "Extruder"
        self._attr_device_info = coordinator.device_info

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        info = self.coordinator.data.get("info")
        if info and hasattr(info, "left_extruder_temperature"):
            return float(info.left_extruder_temperature)
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        info = self.coordinator.data.get("info")
        if info and hasattr(info, "target_left_extruder_temperature"):
            return float(info.target_left_extruder_temperature)
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if self.target_temperature and self.target_temperature > 0:
            return HVACMode.HEAT
        return HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        try:
            await self.coordinator.client.temp_control.set_extruder_temp(
                int(temperature), wait_for=False
            )
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error setting nozzle temperature")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        try:
            if hvac_mode == HVACMode.OFF:
                await self.coordinator.client.temp_control.cancel_extruder_temp()
            elif hvac_mode == HVACMode.HEAT:
                # Set to a default temperature if turning on
                await self.coordinator.client.temp_control.set_extruder_temp(
                    200, wait_for=False
                )
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error setting nozzle HVAC mode")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

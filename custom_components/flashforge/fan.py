"""Fan platform for FlashForge air filtration control."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .data_update_coordinator import FlashForgeDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlashForge fan platform."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    fans = []

    # Add external filtration fan if supported
    if coordinator.client.filtration_control:
        fans.append(FlashForgeExternalFan(coordinator))
        fans.append(FlashForgeInternalFan(coordinator))

    # Add cooling fan
    fans.append(FlashForgeCoolingFan(coordinator))

    # Add chamber fan
    fans.append(FlashForgeChamberFan(coordinator))

    async_add_entities(fans)


class FlashForgeExternalFan(
    CoordinatorEntity[FlashForgeDataUpdateCoordinator], FanEntity
):
    """External filtration fan entity."""

    _attr_has_entity_name = True
    _attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize external fan."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_external_fan"
        self._attr_device_info = coordinator.device_info
        self._attr_name = "External Filtration"

    @property
    def is_on(self) -> bool | None:
        """Return True if fan is on."""
        info = self.coordinator.data.get("info")
        if info is None:
            return None
        return info.external_fan_on

    async def async_turn_on(self) -> None:
        """Turn on the fan."""
        await self.coordinator.client.control.set_external_filtration_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn off the fan."""
        await self.coordinator.client.control.set_filtration_off()
        await self.coordinator.async_request_refresh()


class FlashForgeInternalFan(
    CoordinatorEntity[FlashForgeDataUpdateCoordinator], FanEntity
):
    """Internal filtration fan entity."""

    _attr_has_entity_name = True
    _attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize internal fan."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_internal_fan"
        self._attr_device_info = coordinator.device_info
        self._attr_name = "Internal Filtration"

    @property
    def is_on(self) -> bool | None:
        """Return True if fan is on."""
        info = self.coordinator.data.get("info")
        if info is None:
            return None
        return info.internal_fan_on

    async def async_turn_on(self) -> None:
        """Turn on the fan."""
        await self.coordinator.client.control.set_internal_filtration_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn off the fan."""
        await self.coordinator.client.control.set_filtration_off()
        await self.coordinator.async_request_refresh()


class FlashForgeCoolingFan(
    CoordinatorEntity[FlashForgeDataUpdateCoordinator], FanEntity
):
    """Cooling fan entity with speed control."""

    _attr_has_entity_name = True
    _attr_supported_features = FanEntityFeature.SET_SPEED

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize cooling fan."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_cooling_fan"
        self._attr_device_info = coordinator.device_info
        self._attr_name = "Cooling Fan"

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        info = self.coordinator.data.get("info")
        if info is None:
            return None
        return info.cooling_fan_speed

    @property
    def is_on(self) -> bool | None:
        """Return True if fan is on."""
        return (self.percentage or 0) > 0

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        await self.coordinator.client.control.set_cooling_fan_speed(percentage)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(
        self,
        percentage: int | None = None
    ) -> None:
        """Turn on the fan."""
        speed = percentage if percentage is not None else 100
        await self.async_set_percentage(speed)

    async def async_turn_off(self) -> None:
        """Turn off the fan."""
        await self.async_set_percentage(0)


class FlashForgeChamberFan(
    CoordinatorEntity[FlashForgeDataUpdateCoordinator], FanEntity
):
    """Chamber fan entity with speed control."""

    _attr_has_entity_name = True
    _attr_supported_features = FanEntityFeature.SET_SPEED

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize chamber fan."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_chamber_fan"
        self._attr_device_info = coordinator.device_info
        self._attr_name = "Chamber Fan"

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        info = self.coordinator.data.get("info")
        if info is None:
            return None
        return info.chamber_fan_speed

    @property
    def is_on(self) -> bool | None:
        """Return True if fan is on."""
        return (self.percentage or 0) > 0

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        await self.coordinator.client.control.set_chamber_fan_speed(percentage)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(
        self,
        percentage: int | None = None
    ) -> None:
        """Turn on the fan."""
        speed = percentage if percentage is not None else 100
        await self.async_set_percentage(speed)

    async def async_turn_off(self) -> None:
        """Turn off the fan."""
        await self.async_set_percentage(0)

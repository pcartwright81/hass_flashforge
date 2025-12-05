"""Binary sensor platform for FlashForge."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

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
    """Set up FlashForge binary sensors."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    async_add_entities([FlashForgeDoorSensor(coordinator)])


class FlashForgeDoorSensor(CoordinatorEntity, BinarySensorEntity):
    """Door sensor for FlashForge printer."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize door sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_door"
        self._attr_device_info = coordinator.device_info
        self._attr_name = "Door"

    @property
    def is_on(self) -> bool | None:
        """Return True if door is open."""
        info = self.coordinator.data.get("info")
        if info is None:
            return None
        return info.door_open

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

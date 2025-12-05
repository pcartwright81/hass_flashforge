"""Image platform for FlashForge print thumbnails."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.image import ImageEntity
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
    """Set up FlashForge image platform."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    async_add_entities([FlashForgeThumbnailImage(coordinator)])


class FlashForgeThumbnailImage(
    CoordinatorEntity["FlashForgeDataUpdateCoordinator"], ImageEntity
):
    """Print thumbnail image entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize thumbnail image."""
        # Initialize ImageEntity first to set up access_tokens
        ImageEntity.__init__(self, coordinator.hass)
        # Then initialize CoordinatorEntity using super()
        super().__init__(coordinator)

        self.coordinator: FlashForgeDataUpdateCoordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_thumbnail"
        self._attr_device_info = coordinator.device_info
        self._attr_name = "Print Thumbnail"
        self._attr_content_type = "image/png"

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        thumbnail = self.coordinator.data.get("thumbnail")
        if thumbnail:
            return thumbnail
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get("thumbnail") is not None
        )

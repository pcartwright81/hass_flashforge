"""Support for FlashForge selects."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data_update_coordinator import FlashForgeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlashForge select based on a config entry."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SelectEntity] = [
        FlashForgeFileSelect(coordinator),
    ]

    # Add filtration select only if equipped
    if coordinator.client.filtration_control:
        entities.append(FlashForgeFiltrationSelect(coordinator))

    async_add_entities(entities)


class FlashForgeFileSelect(
    CoordinatorEntity["FlashForgeDataUpdateCoordinator"], SelectEntity
):
    """Representation of file selection entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the file select entity."""
        super().__init__(coordinator)
        self.coordinator: FlashForgeDataUpdateCoordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_select"
        self._attr_icon = "mdi:file-cad"
        self._attr_name = "File List"
        self._attr_device_info = coordinator.device_info

        # Initialize with files from coordinator
        files = coordinator.data.get("files", [])
        self._attr_options = self._clean_file_list(files) if files else ["No files"]
        self._attr_current_option = (
            self._attr_options[0] if self._attr_options else None
        )

    def _clean_file_list(self, files: list[str]) -> list[str]:
        """Clean file names by removing /data/ prefix."""
        cleaned = []
        for file in files:
            if isinstance(file, str):
                cleaned.append(file.removeprefix("/data/"))
            else:
                cleaned.append(str(file))
        return cleaned if cleaned else ["No files"]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        files = self.coordinator.data.get("files", [])
        cleaned_files = self._clean_file_list(files) if files else ["No files"]

        # Only update if files have changed
        if cleaned_files != self._attr_options:
            self._attr_options = cleaned_files
            # Keep current selection if still valid, otherwise select first
            if self._attr_current_option not in self._attr_options:
                self._attr_current_option = (
                    self._attr_options[0] if self._attr_options else None
                )

        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Update the current selected option."""
        if option in self._attr_options:
            self._attr_current_option = option
            self.async_write_ha_state()
            _LOGGER.debug("Selected file: %s", option)
        else:
            _LOGGER.warning("Attempted to select invalid option: %s", option)


class FlashForgeFiltrationSelect(
    CoordinatorEntity["FlashForgeDataUpdateCoordinator"], SelectEntity
):
    """Representation of filtration mode selector."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_options: ClassVar[list[str]] = ["Off", "Internal", "External"]
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize the filtration select entity."""
        super().__init__(coordinator)
        self.coordinator: FlashForgeDataUpdateCoordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_filtration_mode"
        self._attr_name = "Filtration Mode"
        self._attr_device_info = coordinator.device_info
        self._attr_current_option = "Off"

    async def async_select_option(self, option: str) -> None:
        """Change the selected filtration mode."""
        try:
            if option == "Off":
                await self.coordinator.client.control.set_filtration_off()
            elif option == "Internal":
                await self.coordinator.client.control.set_internal_filtration_on()
            elif option == "External":
                await self.coordinator.client.control.set_external_filtration_on()
            else:
                _LOGGER.warning("Invalid filtration option: %s", option)
                return

            self._attr_current_option = option
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
            _LOGGER.debug("Filtration mode set to: %s", option)
        except Exception:
            _LOGGER.exception("Error setting filtration mode to %s", option)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.client.filtration_control
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

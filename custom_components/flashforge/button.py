"""Button platform that offers a PrinterButton entity."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.const import Platform
from homeassistant.helpers import entity_registry

from . import DOMAIN

if TYPE_CHECKING:
    from collections.abc import Callable

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
    """Set up the Printer Button platform."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    async_add_entities(
        [
            PrinterButton(
                name="pause",
                icon="mdi:pause",
                hass=hass,
                coordinator=coordinator,
                action=coordinator.client.job_control.pause_print_job,
            ),
            PrinterButton(
                name="resume",
                icon="mdi:play",
                hass=hass,
                coordinator=coordinator,
                action=coordinator.client.job_control.resume_print_job,
            ),
            PrinterButton(
                name="cancel",
                icon="mdi:stop",
                hass=hass,
                coordinator=coordinator,
                action=coordinator.client.job_control.cancel_print_job,
            ),
            PrinterButton(
                name="clear_platform",
                icon="mdi:broom",
                hass=hass,
                coordinator=coordinator,
                action=coordinator.client.job_control.clear_platform,
            ),
            FilePrinterButton(
                name="print_file",
                icon="mdi:printer-3d-nozzle",
                hass=hass,
                coordinator=coordinator,
                action=coordinator.client.job_control.print_local_file,
            ),
        ]
    )


class PrinterButton(ButtonEntity):
    """Representation of a demo button entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False

    def __init__(
        self,
        name: str,
        icon: str,
        hass: HomeAssistant,  # noqa: ARG002
        coordinator: FlashForgeDataUpdateCoordinator,
        action: Callable,
    ) -> None:
        """Initialize the Demo button entity."""
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{name}"
        self._attr_icon = icon
        self._attr_name = f"{name.replace('_', ' ').title()}"
        self._action = action
        self._attr_device_info = coordinator.device_info
        self.coordinator = coordinator

    async def async_press(self) -> None:
        """Send out a persistent notification."""
        try:
            result = await self._action()
            _LOGGER.debug("Flashforge printer responded with: %s", result)
            # Request coordinator refresh after command
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error executing button action: %s")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success


class FilePrinterButton(PrinterButton):
    """Representation of a file print button entity."""

    async def async_press(self) -> None:
        """Send out a persistent notification."""
        try:
            entityregistry = entity_registry.async_get(self.coordinator.hass)
            select_entity = entityregistry.async_get_entity_id(
                Platform.SELECT,
                DOMAIN,
                f"{self.coordinator.config_entry.unique_id}_select",
            )
            if select_entity is None:
                _LOGGER.warning("No file select entity found")
                return
            select_state = self.coordinator.hass.states.get(select_entity)
            state = select_state.state if select_state else None
            if not state:
                _LOGGER.warning("No file selected")
                return
            result = await self._action(file_name=state, leveling_before_print=False)
            _LOGGER.debug("Flashforge printer responded with: %s", result)
            # Request coordinator refresh after command
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error executing file print action")

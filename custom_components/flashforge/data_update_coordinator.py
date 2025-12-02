"""DataUpdateCoordinator for flashforge integration."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from flashforge import FlashForgeClient

from .const import DEFAULT_NAME, DOMAIN, MAX_FAILED_UPDATES, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class FlashForgeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching FlashForge printer data."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, client: FlashForgeClient, config_entry: ConfigEntry
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DEFAULT_NAME}-{config_entry.entry_id}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
            update_method=self.async_update_data,
        )
        self.config_entry = config_entry
        self.client = client  # Make client accessible to entities
        self.data = {
            "status": None,
            "info": None,
            "files": [],
            "thumbnail": None,
        }
        self.failedupdates = 0

    async def async_update_data(self) -> dict[str, Any]:
        """Update data via API."""
        try:
            info = await self.client.get_printer_status()
            files = await self.client.files.get_local_file_list()

            # Get thumbnail if currently printing
            thumbnail = None
            if info and info.print_file_name:
                try:
                    thumbnail_bytes = await self.client.files.get_gcode_thumbnail(
                        info.print_file_name
                    )
                    if thumbnail_bytes:
                        thumbnail = thumbnail_bytes
                except Exception as e:  # noqa: BLE001
                    _LOGGER.debug("Could not fetch thumbnail: %s", e)

        except (TimeoutError, ConnectionError) as err:
            self.failedupdates += 1
            if self.failedupdates >= MAX_FAILED_UPDATES:
                self.failedupdates = 0
                raise UpdateFailed(err) from err
            return self.data  # Return stale data on intermittent failure

        if not files:
            files = []

        self.failedupdates = 0

        return {
            "status": info.machine_state.value if info else None,
            "info": info,
            "files": files,
            "thumbnail": thumbnail,
        }

    async def async_config_entry_first_refresh(self) -> None:
        """Connect to printer and update with machine info."""
        await self.client.initialize()
        return await super().async_config_entry_first_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        unique_id = self.config_entry.unique_id or ""
        model = self.client.printer_name or "FlashForge"
        name = self.client.printer_name or self.config_entry.title
        firmware = self.client.firmware_version
        sn = self.config_entry.data.get("serial_number", "")
        mac = self.client.mac_address

        return DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="FlashForge",
            model=model,
            name=name,
            sw_version=firmware,
            serial_number=sn,
            hw_version=mac,
        )

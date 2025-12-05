"""FlashForge camera integration."""

from __future__ import annotations

import logging
from contextlib import closing
from typing import TYPE_CHECKING

import requests
from homeassistant.components.camera import Camera
from homeassistant.helpers.aiohttp_client import (
    async_aiohttp_proxy_web,
    async_get_clientsession,
)

from .const import DOMAIN

if TYPE_CHECKING:
    from collections.abc import Iterable

    from aiohttp import web
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    # Assuming FlashForgeDataUpdateCoordinator is imported from a local file
    from .data_update_coordinator import FlashForgeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def extract_image_from_mjpeg(stream: Iterable[bytes]) -> bytes | None:
    """Take in a MJPEG stream object, return the jpg from it."""
    data = b""

    for chunk in stream:
        data += chunk
        # JPEG End-of-Image marker
        jpg_end = data.find(b"\xff\xd9")

        if jpg_end == -1:
            continue

        # JPEG Start-of-Image marker
        jpg_start = data.find(b"\xff\xd8")

        if jpg_start == -1:
            continue

        return data[jpg_start : jpg_end + 2]
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the available FlashForge camera platform."""
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities([FlashForgeCamera(coordinator)])


class FlashForgeCamera(Camera):
    """FlashForge camera object."""

    def __init__(self, coordinator: FlashForgeDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__()
        self.coordinator = coordinator

        self._attr_device_info = coordinator.device_info
        self._attr_name = "Camera"
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_camera"
        self._attr_is_streaming = True

    @property
    def _mjpeg_url(self) -> str | None:
        """Dynamically retrieve the camera stream URL from the nested FFMachineInfo."""
        printer_info = self.coordinator.data.get("info")

        if printer_info:
            return printer_info.camera_stream_url

        return None

    def camera_image(
        self,
        width: int | None = None,  # noqa: ARG002
        height: int | None = None,  # noqa: ARG002
    ) -> bytes | None:
        """Return a still image response from the camera."""
        mjpeg_url = self._mjpeg_url

        if not self.available or not mjpeg_url:
            self._attr_is_streaming = False
            _LOGGER.warning(
                "Still image unavailable for %s camera: offline or URL not set",
                self._attr_name,
            )
            return None

        try:
            # Use the dynamically fetched URL
            req = requests.get(mjpeg_url, stream=True, timeout=10)

            with closing(req) as response:
                return extract_image_from_mjpeg(response.iter_content(102400))
        except requests.exceptions.ConnectionError:
            self._attr_is_streaming = False
            return None

    async def handle_async_mjpeg_stream(
        self, request: web.Request
    ) -> web.StreamResponse | None:
        """Generate an HTTP MJPEG stream from the camera."""
        mjpeg_url = self._mjpeg_url

        if not self.available or not mjpeg_url:
            self._attr_is_streaming = False
            _LOGGER.warning(
                "Live stream unavailable for %s camera: offline or URL not set",
                self._attr_name,
            )
            return None

        # connect to stream
        websession = async_get_clientsession(self.hass)
        # Use the dynamically fetched URL
        stream_coro = websession.get(mjpeg_url)

        return await async_aiohttp_proxy_web(self.hass, request, stream_coro)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # The stream is only available if we have a URL and the coordinator is updated
        return self.coordinator.last_update_success and self._mjpeg_url is not None

"""Fixtures for Flashforge integration tests."""

from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
import pytest_asyncio
from flashforge import MachineState, Temperature
from flashforge.discovery import FlashForgePrinter
from flashforge.models.machine_info import FFMachineInfo
from homeassistant.core import HomeAssistant

from custom_components.flashforge.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


@pytest.fixture
def mock_flashforge_client() -> Generator[MagicMock | AsyncMock]:
    """Change the values that the printer responds with."""
    with (
        patch(
            "custom_components.flashforge.FlashForgeClient", autospec=True
        ) as mock_init_client_class,
        patch(
            "custom_components.flashforge.config_flow.FlashForgeClient",
            new=mock_init_client_class,
        ),
    ):
        # Manually add properties to the spec of the instance mock
        type(mock_init_client_class.return_value).files = PropertyMock()
        type(mock_init_client_class.return_value).job_control = PropertyMock()
        type(mock_init_client_class.return_value).control = PropertyMock()

        mock_instance = mock_init_client_class.return_value
        mock_instance.get_printer_status = AsyncMock(
            return_value=FFMachineInfo(
                name="Adventurer4",
                firmware_version="v2.0.9",
                machine_state=MachineState.PRINTING,
                extruder=Temperature(current=215.0, set=220.0),
                print_bed=Temperature(current=55.0, set=60.0),
                print_progress=50,
                print_file_name="test.gcode",
                current_print_layer=10,
                total_print_layers=100,
                estimated_time=3600,
                print_eta="2025-11-29T19:00:00+00:00",
                print_duration=1800,
            )
        )
        mock_instance.files.get_local_file_list = AsyncMock(return_value=[])
        mock_instance.printer_name = "Adventurer4"
        mock_instance.serial_number = "SNADVA1234567"
        mock_instance.firmware_version = "v2.0.9"
        mock_instance.mac_address = "88:A9:A7:93:86:F8"
        mock_instance.ip_address = "127.0.0.1"
        yield mock_init_client_class


@pytest.fixture
def mock_printer_discovery() -> Generator[Any]:
    """Mock printer discovery."""
    with patch(
        "custom_components.flashforge.config_flow.FlashForgePrinterDiscovery"
    ) as mock_discovery_class:
        mock_discovery_instance = mock_discovery_class.return_value
        mock_discovery_instance.discover_printers_async = AsyncMock(
            return_value=[
                FlashForgePrinter(
                    ip_address="192.168.0.64",
                    serial_number="SNADVA1234567",
                )
            ]
        )
        yield mock_discovery_instance


@pytest_asyncio.fixture(autouse=True)
async def unload_integration(hass: HomeAssistant) -> AsyncGenerator[None]:
    """Try to unload the Flashforge integration after each test."""
    yield

    entries = hass.config_entries.async_entries(DOMAIN)
    if entries:
        entry: ConfigEntry
        for entry in entries:
            await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()

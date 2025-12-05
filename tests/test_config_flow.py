"""Tests for the Flashforge config flow."""

from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from flashforge import MachineState, Temperature
from flashforge.models.machine_info import FFMachineInfo
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_IP_ADDRESS, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.flashforge.const import CONF_SERIAL_NUMBER, DOMAIN

from . import init_integration


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_flashforge_client", "enable_custom_integrations")
async def test_user_flow(hass: HomeAssistant, mock_flashforge_client: MagicMock) -> None:
    """Test the manual user flow."""
    mock_flashforge_client.return_value.get_printer_status.return_value = (
        FFMachineInfo(
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
    mock_flashforge_client.return_value.files.get_local_file_list.return_value = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: config_entries.SOURCE_USER}
    )
    form_result = cast("dict[str, Any]", result)
    assert form_result["type"] is FlowResultType.FORM  # noqa: S101
    assert not form_result["errors"]  # noqa: S101

    # Create the config entry and setup device.
    result = await hass.config_entries.flow.async_configure(
        form_result["flow_id"],
        {
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )

    create_entry_result = cast("dict[str, Any]", result)
    assert create_entry_result["data"][CONF_IP_ADDRESS] == "127.0.0.1"  # noqa: S101
    assert create_entry_result["data"][CONF_SERIAL_NUMBER] == "SNADVA1234567"  # noqa: S101
    assert create_entry_result["title"] == "Adventurer4"  # noqa: S101
    assert create_entry_result["type"] is FlowResultType.CREATE_ENTRY  # noqa: S101
    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries[0].unique_id == "SNADVA1234567"  # noqa: S101


@pytest.mark.enable_socket
@pytest.mark.asyncio
@pytest.mark.usefixtures(
    "mock_flashforge_client", "mock_printer_discovery", "enable_custom_integrations"
)
async def test_user_flow_auto_discover(
    hass: HomeAssistant, mock_flashforge_client: MagicMock
) -> None:
    """Test the auto discovery in manual user flow."""
    mock_flashforge_client.return_value.get_printer_status.return_value = (
        FFMachineInfo(
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
    mock_flashforge_client.return_value.files.get_local_file_list.return_value = []

    # User leaved empty form fields to trigger auto discover.
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data={},
    )

    # Assert that we found mocked printer.
    form_result = cast("dict[str, Any]", result)
    assert form_result["type"] is FlowResultType.FORM  # noqa: S101
    assert form_result["description_placeholders"] == {  # noqa: S101
        "machine_name": "Adventurer4",
        "ip_addr": "192.168.0.64",
    }
    assert form_result["step_id"] == "auto_confirm"  # noqa: S101
    progress = hass.config_entries.flow.async_progress()
    assert len(progress) == 1  # noqa: S101
    progress_item = cast("dict[str, Any]", progress[0])
    assert progress_item["flow_id"] == form_result["flow_id"]  # noqa: S101
    assert progress_item["context"]["confirm_only"] is True  # noqa: S101

    # User confirm to add this device.
    result = await hass.config_entries.flow.async_configure(
        form_result["flow_id"], user_input={}
    )
    # Assert everything is ok.
    create_entry_result = cast("dict[str, Any]", result)
    assert create_entry_result["data"][CONF_IP_ADDRESS] == "192.168.0.64"  # noqa: S101
    assert create_entry_result["data"][CONF_SERIAL_NUMBER] == "SNADVA1234567"  # noqa: S101
    assert create_entry_result["title"] == "Adventurer4"  # noqa: S101
    assert create_entry_result["type"] is FlowResultType.CREATE_ENTRY  # noqa: S101


@pytest.mark.enable_socket
@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_flashforge_client", "enable_custom_integrations")
async def test_auto_discover_no_devices(
    hass: HomeAssistant,
    mock_printer_discovery: MagicMock,
    mock_flashforge_client: MagicMock,
) -> None:
    """Test the auto discovery didn't find any devices."""
    mock_printer_discovery.discover_printers_async.return_value = []
    mock_flashforge_client.return_value.get_printer_status.return_value = (
        FFMachineInfo(
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
    mock_flashforge_client.return_value.files.get_local_file_list.return_value = []

    # User leaved empty form fields to trigger auto discover.
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data={},
    )

    # Assert that no devices discovered.
    abort_result = cast("dict[str, Any]", result)
    assert abort_result["reason"] == "no_devices_found"  # noqa: S101
    assert abort_result["type"] is FlowResultType.ABORT  # noqa: S101


@pytest.mark.enable_socket
@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_printer_discovery", "enable_custom_integrations")
async def test_auto_discover_device_error(
    hass: HomeAssistant,
    mock_flashforge_client: MagicMock,
) -> None:
    """Test the auto discovery found a device that's not responing as expected."""
    mock_flashforge_client.return_value.get_printer_status.side_effect = TimeoutError(
        "timeout"
    )

    # User leaved empty form fields to trigger auto discover.
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data={},
    )

    # Assert that no devices discovered.
    abort_result = cast("dict[str, Any]", result)
    assert abort_result["reason"] == "cannot_connect"  # noqa: S101
    assert abort_result["type"] is FlowResultType.ABORT  # noqa: S101


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_custom_integrations")
async def test_connection_timeout(
    hass: HomeAssistant,
    mock_flashforge_client: MagicMock,
) -> None:
    """Test what happens if there is a connection timeout."""
    mock_flashforge_client.side_effect = TimeoutError("timeout")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data={
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    form_result = cast("dict[str, Any]", result)
    assert form_result["type"] is FlowResultType.FORM  # noqa: S101
    assert form_result["errors"] == {CONF_IP_ADDRESS: "cannot_connect"}  # noqa: S101


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_custom_integrations")
async def test_connection_error(
    hass: HomeAssistant, mock_flashforge_client: MagicMock
) -> None:
    """Test what happens if there is a connection Error."""
    mock_flashforge_client.side_effect = ConnectionError("conn_error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data={
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    form_result = cast("dict[str, Any]", result)
    assert form_result["type"] is FlowResultType.FORM  # noqa: S101
    assert form_result["errors"] == {CONF_IP_ADDRESS: "cannot_connect"}  # noqa: S101


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_flashforge_client", "enable_custom_integrations")
async def test_user_device_exists_abort(
    hass: HomeAssistant, mock_flashforge_client: MagicMock
) -> None:
    """Test if device is already configured."""
    mock_flashforge_client.return_value.get_printer_status.return_value = (
        FFMachineInfo(
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
    mock_flashforge_client.return_value.files.get_local_file_list.return_value = []

    await init_integration(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data={
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    abort_result = cast("dict[str, Any]", result)
    assert abort_result["type"] is FlowResultType.ABORT  # noqa: S101
    assert abort_result["reason"] == "already_configured"  # noqa: S101


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_flashforge_client", "enable_custom_integrations")
async def test_unload_integration(
    hass: HomeAssistant, mock_flashforge_client: MagicMock
) -> None:
    """Test of unload integration."""
    mock_flashforge_client.return_value.get_printer_status.return_value = (
        FFMachineInfo(
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
    mock_flashforge_client.return_value.files.get_local_file_list.return_value = []

    entry = await init_integration(hass)

    assert entry.state is ConfigEntryState.LOADED  # noqa: S101
    await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED  # noqa: S101


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_custom_integrations")
async def test_printer_not_responding(
    hass: HomeAssistant, mock_flashforge_client: MagicMock
) -> None:
    """Test if printer not responding during setup."""
    mock_flashforge_client.return_value.get_printer_status.side_effect = ConnectionError(
        "conn_error"
    )
    entry = await init_integration(hass)

    assert entry.state is ConfigEntryState.SETUP_RETRY  # noqa: S101

    mock_flashforge_client.return_value.get_printer_status.side_effect = TimeoutError("timeout")
    entry = await init_integration(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY  # noqa: S101
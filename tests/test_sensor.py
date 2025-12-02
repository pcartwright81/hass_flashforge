"""Tests for the Flashforge sensors."""

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry

from custom_components.flashforge.const import DOMAIN, MAX_FAILED_UPDATES

from . import init_integration

if TYPE_CHECKING:
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

SENSORS = (
    {
        "entity_id": "sensor.adventurer4_extruder_temp",
        "state": "215.0",
        "name": "Adventurer4 Extruder Temp",
        "unique_id": "SNADVA1234567_extruder_temp",
    },
    {
        "entity_id": "sensor.adventurer4_extruder_target_temp",
        "state": "220.0",
        "name": "Adventurer4 Extruder Target Temp",
        "unique_id": "SNADVA1234567_extruder_target_temp",
    },
    {
        "entity_id": "sensor.adventurer4_bed_temp",
        "state": "55.0",
        "name": "Adventurer4 Bed Temp",
        "unique_id": "SNADVA1234567_bed_temp",
    },
    {
        "entity_id": "sensor.adventurer4_bed_target_temp",
        "state": "60.0",
        "name": "Adventurer4 Bed Target Temp",
        "unique_id": "SNADVA1234567_bed_target_temp",
    },
    {
        "entity_id": "sensor.adventurer4_status",
        "state": "printing",
        "name": "Adventurer4 Status",
        "unique_id": "SNADVA1234567_status",
    },
    {
        "entity_id": "sensor.adventurer4_job_percentage",
        "state": "50.0",
        "name": "Adventurer4 Job Percentage",
        "unique_id": "SNADVA1234567_job_percentage",
    },
    {
        "entity_id": "sensor.adventurer4_current_layer",
        "state": "10",
        "name": "Adventurer4 Current Layer",
        "unique_id": "SNADVA1234567_current_layer",
    },
    {
        "entity_id": "sensor.adventurer4_total_layers",
        "state": "100",
        "name": "Adventurer4 Total Layers",
        "unique_id": "SNADVA1234567_total_layers",
    },
    {
        "entity_id": "sensor.adventurer4_print_time_remaining",
        "state": "3600",
        "name": "Adventurer4 Print Time Remaining",
        "unique_id": "SNADVA1234567_print_time_remaining",
    },
    {
        "entity_id": "sensor.adventurer4_print_eta",
        "state": "2025-11-29T19:00:00+00:00",
        "name": "Adventurer4 Print Eta",
        "unique_id": "SNADVA1234567_print_eta",
    },
    {
        "entity_id": "sensor.adventurer4_print_duration",
        "state": "1800",
        "name": "Adventurer4 Print Duration",
        "unique_id": "SNADVA1234567_print_duration",
    },
)


@pytest.mark.asyncio
async def test_sensors(
    hass: HomeAssistant,
    mock_flashforge_client: MagicMock,  # noqa: ARG001
    enable_custom_integrations: Any,  # noqa: ARG001
) -> None:
    """Test Flashforge sensors."""
    entry = await init_integration(hass)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED  # noqa: S101
    registry = entity_registry.async_get(hass)

    for expected in SENSORS:
        state = hass.states.get(expected["entity_id"])
        assert state is not None  # noqa: S101
        assert state.state == expected["state"]  # noqa: S101
        assert state.name == expected["name"]  # noqa: S101
        entity = registry.async_get(expected["entity_id"])
        assert entity is not None  # noqa: S101
        assert entity.unique_id == expected["unique_id"]  # noqa: S101


@pytest.mark.asyncio
async def test_unload_integration_and_sensors(
    hass: HomeAssistant,
    mock_flashforge_client: MagicMock,  # noqa: ARG001
    enable_custom_integrations: Any,  # noqa: ARG001
) -> None:
    """Test Flashforge sensors are unavailable and then deleted when integration."""
    entry = await init_integration(hass)
    await hass.async_block_till_done()

    # Sensor become unavailable when integration unloads.
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    for sensor in SENSORS:
        state = hass.states.get(sensor["entity_id"])
        assert state is not None  # noqa: S101
        assert state.state == STATE_UNAVAILABLE  # noqa: S101

    # Sensor become None when integration is deleted.
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get(SENSORS[0]["entity_id"])
    assert state is None  # noqa: S101


@pytest.mark.asyncio
async def test_sensor_update_error(
    hass: HomeAssistant,
    mock_flashforge_client: MagicMock,
    enable_custom_integrations: Any,  # noqa: ARG001
) -> None:
    """Test Flashforge sensors are unavailable after an update error."""
    entry = await init_integration(hass)
    await hass.async_block_till_done()

    # Change printer respond.
    mock_flashforge_client.return_value.get_printer_status.side_effect = (
        ConnectionError("conn_error")
    )

    # Request sensor update.
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    for _ in range(MAX_FAILED_UPDATES):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    for sensor in SENSORS:
        state = hass.states.get(sensor["entity_id"])
        assert state is not None  # noqa: S101
        assert state.state == STATE_UNAVAILABLE  # noqa: S101


@pytest.mark.asyncio
async def test_sensor_update_error2(
    hass: HomeAssistant,
    mock_flashforge_client: MagicMock,
    enable_custom_integrations: Any,  # noqa: ARG001
) -> None:
    """Test Flashforge sensors are unavailable after an update error."""
    entry = await init_integration(hass)
    await hass.async_block_till_done()
    init_call_count = 1  # First refresh

    # Change printer respond.
    mock_flashforge_client.return_value.get_printer_status.side_effect = TimeoutError(
        "timeout"
    )

    # Request sensor update.
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    for _ in range(MAX_FAILED_UPDATES):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    assert (  # noqa: S101
        mock_flashforge_client.return_value.get_printer_status.call_count
        == init_call_count + MAX_FAILED_UPDATES
    )
    for sensor in SENSORS:
        state = hass.states.get(sensor["entity_id"])
        assert state is not None  # noqa: S101
        assert state.state == STATE_UNAVAILABLE  # noqa: S101

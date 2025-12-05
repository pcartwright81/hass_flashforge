"""Tests for the Flashforge integration."""

from typing import Any

import pytest
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.flashforge.const import CONF_SERIAL_NUMBER, DOMAIN


def get_schema_default(schema: dict, key_name: str) -> Any:
    """Return default value from a schema."""
    for schema_key in schema:
        if schema_key == key_name:
            if schema_key.default is not vol.UNDEFINED:
                return schema_key.default()
            msg = f"{key_name} doesn't have a default."
            raise AttributeError(msg)
    msg = f"{key_name} not in schema."
    raise KeyError(msg)


def get_schema_suggested(schema: dict, key_name: str) -> Any:
    """Return suggested value from a schema."""
    for schema_key in schema:
        if schema_key == key_name:
            if (
                isinstance(schema_key.description, dict)
                and "suggested_value" in schema_key.description
            ):
                return schema_key.description["suggested_value"]
            msg = f"{key_name} doesn't have a suggested value."
            raise AttributeError(msg)
    msg = f"{key_name} not in schema."
    raise KeyError(msg)


@pytest.mark.asyncio
async def init_integration(
    hass: HomeAssistant, *, skip_setup: bool = False
) -> ConfigEntry:
    """Set up a Flashforge printer in Home Assistant."""
    entry = MockConfigEntry(
        title="Adventurer4",
        domain=DOMAIN,
        unique_id="SNADVA1234567",
        data={
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_SERIAL_NUMBER: "SNADVA1234567",
        },
    )

    entry.add_to_hass(hass)

    if not skip_setup:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry

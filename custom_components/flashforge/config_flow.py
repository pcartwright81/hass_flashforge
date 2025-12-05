"""Config flow for Flashforge."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import callback

from flashforge import FlashForgeClient, FlashForgePrinterDiscovery

from .const import CONF_CHECK_CODE, CONF_SERIAL_NUMBER, DOMAIN

_LOGGER = logging.getLogger(__name__)


class FlashForgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""

    VERSION = 1

    ip_addr: str | None
    serial: str
    check_code: str
    machine_name: str
    client: FlashForgeClient

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Run when user trying to add component."""
        errors = {}
        self.ip_addr = None
        self.check_code = ""
        self.serial = ""
        self.machine_name = ""

        if user_input is not None:
            if CONF_IP_ADDRESS not in user_input:
                # Try to discover printers on network
                return await self.async_step_auto()

            self.ip_addr = user_input[CONF_IP_ADDRESS]
            self.serial = user_input.get(CONF_SERIAL_NUMBER, "")
            self.check_code = user_input.get(CONF_CHECK_CODE, "")

            try:
                await self._get_printer_info(user_input)
                return self._async_create_entry()
            except (TimeoutError, ConnectionError):
                errors[CONF_IP_ADDRESS] = "cannot_connect"

        return self._async_show_form(errors=errors)

    async def async_step_auto(self) -> ConfigFlowResult:
        """Try to discover ip of printer and return a confirm form."""
        _LOGGER.debug("Starting auto-discovery for FlashForge printers.")
        ip: str | None = None
        discovered_printers = []

        discovery = FlashForgePrinterDiscovery()
        try:
            discovered_printers = await discovery.discover_printers_async(
                timeout_ms=20000,
                idle_timeout_ms=3000,
                max_retries=3,
            )
            _LOGGER.debug(
                "Discovery found %s printer(s): %s",
                len(discovered_printers),
                discovered_printers,
            )
        except Exception as e:  # pylint: disable=broad-except-clause
            _LOGGER.exception("Error during FlashForge printer discovery: %s", e)
            return self.async_abort(reason="discovery_error")

        if discovered_printers:
            printer_info = discovered_printers[0]
            ip = printer_info.ip_address
            self.serial = printer_info.serial_number or ""
            _LOGGER.debug(
                "Selected first discovered printer: %s at %s (Serial: %s)",
                printer_info.name,
                ip,
                self.serial,
            )

        if ip is None:
            _LOGGER.debug("No FlashForge printers found during auto-discovery.")
            return self.async_abort(reason="no_devices_found")

        try:
            await self._get_printer_info(
                {
                    CONF_IP_ADDRESS: ip,
                    CONF_SERIAL_NUMBER: self.serial,
                    CONF_CHECK_CODE: "",
                }
            )
        except (TimeoutError, ConnectionError) as e:
            _LOGGER.debug(
                "Failed to get printer info for discovered device %s: %s", ip, e
            )
            return self.async_abort(reason="cannot_connect")

        self._set_confirm_only()
        title = self.machine_name or self.serial or ""
        return self.async_show_form(
            step_id="auto_confirm",
            description_placeholders={
                "machine_name": title,
                "ip_addr": ip,
            },
        )

    async def async_step_auto_confirm(
        self, _: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """User confirmed to add device to Home Assistant."""
        return self._async_create_entry()

    @callback
    def _async_show_form(
        self,
        errors: dict[str, str] | None = None,
    ) -> ConfigFlowResult:
        """Create and show the form for user."""
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_IP_ADDRESS,
                    description={"suggested_value": self.ip_addr},
                ): str,
                vol.Optional(CONF_SERIAL_NUMBER, default=""): str,
                vol.Optional(CONF_CHECK_CODE, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors or {},
        )

    async def _get_printer_info(self, user_input: dict) -> None:
        """Try to get info from given ip."""
        self.ip_addr = user_input[CONF_IP_ADDRESS]
        self.serial = user_input.get(CONF_SERIAL_NUMBER, "")
        self.check_code = user_input.get(CONF_CHECK_CODE, "")

        # FlashForgeClient from flashforge-python-api connects on instantiation
        # No initialize() method exists in the library
        self.client = FlashForgeClient(str(self.ip_addr), self.serial, self.check_code)

        # Get printer information if available
        try:
            if hasattr(self.client, "printer_name") and self.client.printer_name:
                self.machine_name = self.client.printer_name
            if not self.serial and hasattr(self.client, "serial_number"):
                self.serial = self.client.serial_number or ""
        except AttributeError:
            # If attributes don't exist, continue without them
            pass

        await self.async_set_unique_id(self.serial)
        self._abort_if_unique_id_configured(
            updates={
                CONF_IP_ADDRESS: self.ip_addr,
                CONF_SERIAL_NUMBER: self.serial,
                CONF_CHECK_CODE: self.check_code,
            }
        )

    @callback
    def _async_create_entry(self) -> ConfigFlowResult:
        """Create config entry."""
        title = self.machine_name or self.serial or ""
        return self.async_create_entry(
            title=title,
            data={
                CONF_IP_ADDRESS: self.ip_addr,
                CONF_SERIAL_NUMBER: self.serial,
                CONF_CHECK_CODE: self.check_code,
            },
        )

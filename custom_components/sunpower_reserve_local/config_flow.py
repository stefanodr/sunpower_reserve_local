"""Config flow for SunPower Reserve Local."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_UNIT,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .modbus import ModbusError, ReadOnlyModbusClient

SOC_REGISTER = 0x0102


class SunPowerReserveConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return SunPowerReserveOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            client = ReadOnlyModbusClient(
                user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_UNIT]
            )
            try:
                await client.read_once(SOC_REGISTER, 1)
            except ModbusError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"SunPower Reserve ({user_input[CONF_HOST]})",
                    data=user_input,
                )
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_UNIT, default=DEFAULT_UNIT): vol.All(
                    int, vol.Range(min=1, max=247)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class SunPowerReserveOptionsFlow(OptionsFlow):
    """Options: polling interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

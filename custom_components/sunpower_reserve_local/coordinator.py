"""Data update coordinator (read-only Modbus polling)."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, CONF_UNIT, DEFAULT_SCAN_INTERVAL, DOMAIN
from .modbus import ModbusError, ReadOnlyModbusClient
from .registers import BLOCK_SIZE, BLOCKS, decode

_LOGGER = logging.getLogger(__name__)


class SunPowerReserveCoordinator(DataUpdateCoordinator[dict[str, float | None]]):
    """Poll the inverter over Modbus TCP (function code 3 only)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client = ReadOnlyModbusClient(
            entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_UNIT]
        )

    async def _async_update_data(self) -> dict[str, float | None]:
        try:
            registers, refused = await self.client.read_blocks(BLOCKS, BLOCK_SIZE)
        except ModbusError as err:
            raise UpdateFailed(f"Inverter not reachable: {err}") from err
        if refused:
            _LOGGER.debug("Blocks refused by the inverter: %s", [hex(a) for a in refused])
        if not registers:
            raise UpdateFailed("No data received from the inverter")
        return decode(registers)

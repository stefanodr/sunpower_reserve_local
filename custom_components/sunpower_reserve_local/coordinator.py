"""Data update coordinator (read-only Modbus polling)."""

from __future__ import annotations

from datetime import timedelta
import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HOUSE_OFFSET,
    CONF_PV_OFFSET,
    CONF_SCAN_INTERVAL,
    CONF_UNIT,
    CONF_USABLE_CAPACITY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USABLE_CAPACITY,
    DOMAIN,
)
from .energy import EnergyAccumulator
from .modbus import ModbusError, ReadOnlyModbusClient
from .registers import BLOCK_SIZE, BLOCKS, decode

_LOGGER = logging.getLogger(__name__)


class SunPowerReserveCoordinator(DataUpdateCoordinator[dict[str, float | str | None]]):
    """Poll the inverter over Modbus TCP (function code 3 only)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=interval),
        )
        self._store: Store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self._entry = entry
        self._energy = EnergyAccumulator(max_gap=3 * interval)
        self._configure_energy()
        self.client = ReadOnlyModbusClient(
            entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_UNIT]
        )

    async def async_load_state(self) -> None:
        """Restore integrated totals and period baselines."""
        saved = await self._store.async_load()
        self._energy = EnergyAccumulator(self._energy.max_gap, saved)
        self._configure_energy()

    def _configure_energy(self) -> None:
        options = self._entry.options
        self._energy.offsets = {
            "pv_energy": float(options.get(CONF_PV_OFFSET, 0.0)),
            "house_energy": float(options.get(CONF_HOUSE_OFFSET, 0.0)),
        }
        self._energy.usable_capacity = float(
            options.get(CONF_USABLE_CAPACITY, DEFAULT_USABLE_CAPACITY)
        )

    async def async_save_state(self) -> None:
        """Persist totals immediately (called on unload)."""
        await self._store.async_save(self._energy.to_dict())

    async def _async_update_data(self) -> dict[str, float | str | None]:
        try:
            registers, refused = await self.client.read_blocks(BLOCKS, BLOCK_SIZE)
        except ModbusError as err:
            raise UpdateFailed(f"Inverter not reachable: {err}") from err
        if refused:
            _LOGGER.debug("Blocks refused by the inverter: %s", [hex(a) for a in refused])
        if not registers:
            raise UpdateFailed("No data received from the inverter")
        data = decode(registers)
        self._energy.update(data, dt_util.now(), time.monotonic())
        self._store.async_delay_save(self._energy.to_dict, 60)
        return data

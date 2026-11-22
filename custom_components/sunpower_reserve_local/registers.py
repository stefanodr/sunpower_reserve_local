"""Register map of the SunPower Reserve (AlphaESS) inverter. HA independent."""

from __future__ import annotations

from dataclasses import dataclass

BLOCK_SIZE = 8
BLOCKS = [
    0x0010, 0x0018,
    0x0100, 0x0108, 0x0110, 0x0120,
    0x0400, 0x0408, 0x0418, 0x0420, 0x0430,
]  # fmt: skip


@dataclass(frozen=True)
class Reg:
    key: str
    address: int
    kind: str  # u16 | s16 | u32 | s32 (32 bit: high word first)
    scale: float
    unit: str | None
    device_class: str | None
    state_class: str | None
    enabled: bool = True  # False = experimental / diagnostic
    precision: int | None = None


M, T = "measurement", "total_increasing"

REGISTERS: list[Reg] = [
    # Grid / meter
    Reg("grid_energy_export", 0x0010, "u32", 0.01, "kWh", "energy", T, True, 2),
    Reg("grid_energy_import", 0x0012, "u32", 0.01, "kWh", "energy", T, True, 2),
    Reg("grid_voltage", 0x0014, "u16", 1, "V", "voltage", M, True, 0),
    Reg("grid_current", 0x0017, "s16", 0.1, "A", "current", M, False, 1),
    Reg("grid_frequency", 0x001A, "u16", 0.01, "Hz", "frequency", M, True, 2),
    Reg("grid_power", 0x001B, "s32", 1, "W", "power", M, True, 0),
    # Battery
    Reg("battery_voltage", 0x0100, "u16", 0.1, "V", "voltage", M, True, 1),
    Reg("battery_current", 0x0101, "s16", 0.1, "A", "current", M, True, 1),
    Reg("battery_soc", 0x0102, "u16", 0.1, "%", "battery", M, True, 1),
    Reg("battery_power", 0x0126, "s16", 1, "W", "power", M, True, 0),
    Reg("battery_energy_charged", 0x0120, "u32", 0.1, "kWh", "energy", T, True, 1),
    Reg("battery_energy_discharged", 0x0122, "u32", 0.1, "kWh", "energy", T, True, 1),
    Reg("battery_energy_charged_from_grid", 0x0124, "u32", 0.1, "kWh", "energy", T, False, 1),
    Reg("battery_cell_voltage_1", 0x0107, "u16", 1, "mV", "voltage", M, False, 0),
    Reg("battery_cell_voltage_2", 0x010A, "u16", 1, "mV", "voltage", M, False, 0),
    Reg("battery_max_charge_current", 0x0111, "u16", 0.1, "A", "current", M, False, 1),
    Reg("battery_max_discharge_current", 0x0112, "u16", 0.1, "A", "current", M, False, 1),
    # Inverter
    Reg("inverter_voltage", 0x0400, "u16", 0.1, "V", "voltage", M, True, 1),
    Reg("inverter_power_l1", 0x0406, "s32", 1, "W", "power", M, False, 0),
    Reg("inverter_power", 0x040C, "s32", 1, "W", "power", M, True, 0),
    Reg("inverter_temperature", 0x0435, "s16", 0.1, "°C", "temperature", M, False, 1),
    # PV
    Reg("pv1_voltage", 0x041D, "u16", 0.1, "V", "voltage", M, True, 1),
    Reg("pv1_current", 0x041E, "u16", 0.1, "A", "current", M, True, 1),
    Reg("pv1_power", 0x041F, "s32", 1, "W", "power", M, True, 0),
    Reg("pv2_voltage", 0x0421, "u16", 0.1, "V", "voltage", M, True, 1),
    Reg("pv2_current", 0x0422, "u16", 0.1, "A", "current", M, True, 1),
    Reg("pv2_power", 0x0423, "s32", 1, "W", "power", M, True, 0),
]

# Derived sensors: key -> (unit, device_class, state_class, enabled, precision)
DERIVED = {
    "pv_power": ("W", "power", M, True, 0),
    "house_load": ("W", "power", M, False, 0),
}


def _signed(value: int, bits: int) -> int:
    return value - (1 << bits) if value >= 1 << (bits - 1) else value


def _decode(reg: Reg, regs: dict[int, int]) -> float | None:
    width = 2 if reg.kind.endswith("32") else 1
    words = [regs.get(reg.address + i) for i in range(width)]
    if any(w is None for w in words):
        return None
    raw = words[0] if width == 1 else (words[0] << 16) | words[1]
    if reg.kind.startswith("s"):
        raw = _signed(raw, 16 * width)
    value = raw * reg.scale
    return round(value, reg.precision) if reg.precision is not None else value


def decode(regs: dict[int, int]) -> dict[str, float | None]:
    """Decode raw registers into sensor values."""
    data = {reg.key: _decode(reg, regs) for reg in REGISTERS}
    p1, p2 = data["pv1_power"], data["pv2_power"]
    data["pv_power"] = None if p1 is None or p2 is None else p1 + p2
    # house load = PV + battery discharge + grid import
    # (battery_power: negative = charging; grid_power: negative = export)
    batt, grid = data["battery_power"], data["grid_power"]
    data["house_load"] = (
        None if p1 is None or p2 is None or batt is None or grid is None
        else p1 + p2 + batt + grid
    )
    return data

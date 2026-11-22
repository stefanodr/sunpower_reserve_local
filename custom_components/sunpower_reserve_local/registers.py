"""Register map of the SunPower Reserve (AlphaESS) inverter. HA independent."""

from __future__ import annotations

from dataclasses import dataclass

BLOCK_SIZE = 8
BLOCKS = [
    0x0010, 0x0018,
    0x0100, 0x0108, 0x0110, 0x0120,
    0x0400, 0x0408, 0x0418, 0x0420, 0x0430,
]  # fmt: skip

# Static information (versions, serial, configuration): read at start and then
# only once an hour.
STATIC_BLOCKS = [0x0640, 0x0648, 0x0650, 0x0748, 0x0800, 0x08A0]
STATIC_ADDRESSES = {a for start in STATIC_BLOCKS for a in range(start, start + BLOCK_SIZE)}


@dataclass(frozen=True)
class Reg:
    key: str
    address: int
    kind: str  # u16 | s16 | u32 | s32 (32 bit: high word first)
    scale: float
    unit: str | None
    device_class: str | None
    state_class: str | None
    enabled: bool = True
    precision: int | None = None
    diagnostic: bool = False


M, T = "measurement", "total_increasing"

REGISTERS: list[Reg] = [
    # Grid / meter
    Reg("grid_energy_export", 0x0010, "u32", 0.01, "kWh", "energy", T, True, 2),
    Reg("grid_energy_import", 0x0012, "u32", 0.01, "kWh", "energy", T, True, 2),
    Reg("grid_voltage", 0x0014, "u16", 1, "V", "voltage", M, True, 0),
    Reg("grid_current", 0x0017, "s16", 0.1, "A", "current", M, True, 1),
    Reg("grid_frequency", 0x001A, "u16", 0.01, "Hz", "frequency", M, True, 2),
    Reg("grid_power", 0x001B, "s32", 1, "W", "power", M, True, 0),
    # Battery
    Reg("battery_voltage", 0x0100, "u16", 0.1, "V", "voltage", M, True, 1),
    Reg("battery_current", 0x0101, "s16", 0.1, "A", "current", M, True, 1),
    Reg("battery_soc", 0x0102, "u16", 0.1, "%", "battery", M, True, 1),
    Reg("battery_power", 0x0126, "s16", 1, "W", "power", M, True, 0),
    Reg("battery_energy_charged", 0x0120, "u32", 0.1, "kWh", "energy", T, True, 1),
    Reg("battery_energy_discharged", 0x0122, "u32", 0.1, "kWh", "energy", T, True, 1),
    Reg("battery_energy_charged_from_grid", 0x0124, "u32", 0.1, "kWh", "energy", T, True, 1),
    Reg("battery_cell_voltage_1", 0x0107, "u16", 1, "mV", "voltage", M, True, 0),
    Reg("battery_cell_voltage_2", 0x010A, "u16", 1, "mV", "voltage", M, True, 0),
    Reg("battery_max_charge_current", 0x0111, "u16", 0.1, "A", "current", M, True, 1),
    Reg("battery_max_discharge_current", 0x0112, "u16", 0.1, "A", "current", M, True, 1),
    # Inverter
    Reg("inverter_voltage", 0x0400, "u16", 0.1, "V", "voltage", M, True, 1),
    Reg("inverter_power_l1", 0x0406, "s32", 1, "W", "power", M, True, 0),
    Reg("inverter_power", 0x040C, "s32", 1, "W", "power", M, True, 0),
    Reg("inverter_temperature", 0x0435, "s16", 0.1, "°C", "temperature", M, True, 1),
    # PV
    Reg("pv1_voltage", 0x041D, "u16", 0.1, "V", "voltage", M, True, 1),
    Reg("pv1_current", 0x041E, "u16", 0.1, "A", "current", M, True, 1),
    Reg("pv1_power", 0x041F, "s32", 1, "W", "power", M, True, 0),
    Reg("pv2_voltage", 0x0421, "u16", 0.1, "V", "voltage", M, True, 1),
    Reg("pv2_current", 0x0422, "u16", 0.1, "A", "current", M, True, 1),
    Reg("pv2_power", 0x0423, "s32", 1, "W", "power", M, True, 0),
    # Static configuration (diagnostic)
    Reg("export_limit", 0x0800, "u16", 1, "%", None, None, True, 0, True),
    Reg("pv_installed_power", 0x0802, "u16", 0.001, "kW", "power", None, True, 1, True),
    Reg("inverter_rated_power", 0x08A3, "u16", 0.001, "kW", "power", None, True, 1, True),
]

# Text sensors (diagnostic): key
TEXT_SENSORS = ["inverter_firmware", "bms_firmware", "ems_firmware"]


def _ascii(regs: dict[int, int], start: int, count: int) -> str | None:
    """Text stored two characters per register (high byte first)."""
    words = [regs.get(start + i) for i in range(count)]
    if any(w is None for w in words):
        return None
    raw = b"".join(w.to_bytes(2, "big") for w in words)
    text = raw.split(b"\0", 1)[0].decode("ascii", errors="ignore").strip()
    return text or None


def decode_static(regs: dict[int, int]) -> dict[str, str | None]:
    """Firmware versions and serial number."""
    bms = regs.get(0x0115)
    ems = [regs.get(a) for a in (0x074B, 0x074C, 0x074D, 0x074F)]
    ems_text = None
    if None not in ems and ems[3] >> 8:
        ems_text = f"V{ems[0]}.{ems[1]}.{ems[2]}{chr(ems[3] >> 8)}"
    return {
        "inverter_firmware": _ascii(regs, 0x0640, 5),
        "bms_firmware": f"V{bms / 100:.2f}" if bms else None,
        "ems_firmware": ems_text,
        "serial_number": _ascii(regs, 0x064A, 8),
    }

# Derived sensors: key -> (unit, device_class, state_class, enabled, precision)
DERIVED = {
    "pv_power": ("W", "power", M, True, 0),
    "house_load": ("W", "power", M, True, 0),
    "battery_stored_energy": ("kWh", "energy_storage", M, True, 2),  # energy.py
    "battery_charge_power": ("W", "power", M, True, 0),
    "battery_discharge_power": ("W", "power", M, True, 0),
    "grid_import_power": ("W", "power", M, True, 0),
    "grid_export_power": ("W", "power", M, True, 0),
    "self_consumption_daily": ("%", None, M, True, 0),  # energy.py
    "self_sufficiency_daily": ("%", None, M, True, 0),  # energy.py
    "battery_time_to_empty": ("h", "duration", M, True, 1),  # energy.py
    "battery_time_to_full": ("h", "duration", M, True, 1),  # energy.py
}

# Below this power (W) the battery / grid is reported as idle
IDLE_THRESHOLD_W = 20

# Text state sensors: key -> allowed values
STATE_SENSORS = {
    "battery_state": ["charging", "discharging", "idle"],
    "grid_state": ["importing", "exporting", "idle"],
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


def decode(regs: dict[int, int]) -> dict[str, float | str | None]:
    """Decode raw registers into sensor values."""
    data: dict[str, float | str | None] = {
        reg.key: _decode(reg, regs) for reg in REGISTERS
    }
    p1, p2 = data["pv1_power"], data["pv2_power"]
    data["pv_power"] = None if p1 is None or p2 is None else p1 + p2
    # house load = PV + battery discharge + grid import
    # (battery_power: negative = charging; grid_power: negative = export)
    batt, grid = data["battery_power"], data["grid_power"]
    data["house_load"] = (
        None if p1 is None or p2 is None or batt is None or grid is None
        else p1 + p2 + batt + grid
    )
    # positive-only power flows (handy for cards that want separate sensors)
    data["battery_charge_power"] = None if batt is None else max(-batt, 0)
    data["battery_discharge_power"] = None if batt is None else max(batt, 0)
    data["grid_import_power"] = None if grid is None else max(grid, 0)
    data["grid_export_power"] = None if grid is None else max(-grid, 0)
    data.update(decode_static(regs))
    # state sensors (battery_power: negative = charging; grid_power: negative = export)
    data["battery_state"] = (
        None if batt is None
        else "discharging" if batt > IDLE_THRESHOLD_W
        else "charging" if batt < -IDLE_THRESHOLD_W
        else "idle"
    )
    data["grid_state"] = (
        None if grid is None
        else "importing" if grid > IDLE_THRESHOLD_W
        else "exporting" if grid < -IDLE_THRESHOLD_W
        else "idle"
    )
    return data

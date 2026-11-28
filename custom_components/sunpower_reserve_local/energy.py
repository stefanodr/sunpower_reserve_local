"""Energy accumulation (integrated totals and period counters). HA independent."""

from __future__ import annotations

from datetime import datetime
from typing import Any

# power sensor -> energy sensor it is integrated into
INTEGRATED: dict[str, str] = {"pv_power": "pv_energy", "house_load": "house_energy"}

PERIODS = ("daily", "weekly", "monthly", "yearly")
PERIOD_SOURCES: dict[str, tuple[str, ...]] = {
    "pv_energy": PERIODS,
    "house_energy": PERIODS,
    "grid_energy_export": PERIODS,
    "grid_energy_import": PERIODS,
    "battery_energy_charged": PERIODS,
    "battery_energy_discharged": PERIODS,
}

DEFAULT_USABLE_CAPACITY = 9.576  # kWh
DEFAULT_BACKUP_RESERVE = 10  # % of charge reserved for the backup line
IDLE_THRESHOLD_W = 20


def period_key(period: str, now: datetime) -> str:
    """Identifier of the period `now` belongs to (local time)."""
    if period == "daily":
        return now.strftime("%Y-%m-%d")
    if period == "weekly":
        year, week, _ = now.isocalendar()
        return f"{year}-W{week:02d}"
    if period == "monthly":
        return now.strftime("%Y-%m")
    return now.strftime("%Y")


def period_sensor_keys() -> list[tuple[str, bool]]:
    """(key, enabled by default) for every period counter."""
    return [
        (f"{source}_{period}", True)
        for source, periods in PERIOD_SOURCES.items()
        for period in periods
    ]


class EnergyAccumulator:
    """Integrates power into energy and keeps per-period counters.

    PV and house energy have no readable total register, so they are integrated
    from power (trapezoid rule, ignoring gaps longer than `max_gap` seconds).
    Grid and battery counters come straight from the inverter registers.
    `offsets` are added to the integrated totals (not to period counters), so
    the totals can be aligned with another source such as the cloud.
    """

    def __init__(self, max_gap: float = 45.0, saved: dict[str, Any] | None = None) -> None:
        saved = saved or {}
        self.max_gap = max_gap
        self.totals: dict[str, float] = {
            k: float(v) for k, v in saved.get("totals", {}).items()
        }
        self.baselines: dict[str, dict[str, Any]] = dict(saved.get("baselines", {}))
        self.offsets: dict[str, float] = {}
        self.usable_capacity: float = DEFAULT_USABLE_CAPACITY
        self.backup_reserve: float = DEFAULT_BACKUP_RESERVE
        self._last: dict[str, tuple[float, float]] = {}

    def to_dict(self) -> dict[str, Any]:
        """State to persist."""
        return {"totals": self.totals, "baselines": self.baselines}

    def update(self, data: dict[str, Any], now: datetime, mono: float) -> None:
        """Add integrated totals and period counters to `data` (in place)."""
        for source, target in INTEGRATED.items():
            power = data.get(source)
            if power is None:
                self._last.pop(source, None)
            else:
                power = max(float(power), 0.0)
                previous = self._last.get(source)
                if previous is not None:
                    dt = mono - previous[0]
                    if 0 < dt <= self.max_gap:
                        self.totals[target] = self.totals.get(target, 0.0) + (
                            (previous[1] + power) / 2 * dt / 3_600_000
                        )
                self._last[source] = (mono, power)
            data[target] = round(
                self.totals.get(target, 0.0) + self.offsets.get(target, 0.0), 3
            )

        soc = data.get("battery_soc")
        data["battery_stored_energy"] = (
            None if soc is None else round(soc / 100 * self.usable_capacity, 2)
        )
        # energy that can really be discharged: the backup reserve is not usable
        data["battery_usable_energy"] = (
            None
            if soc is None
            else round(max(soc - self.backup_reserve, 0) / 100 * self.usable_capacity, 2)
        )

        for source, periods in PERIOD_SOURCES.items():
            # period counters use offset-free values
            value = self.totals.get(source, 0.0) if source in INTEGRATED.values() else data.get(source)
            for period in periods:
                key = f"{source}_{period}"
                if value is None:
                    data[key] = None
                    continue
                pid = period_key(period, now)
                base = self.baselines.get(key)
                if not base or base.get("period") != pid or value < base["start"]:
                    base = {"period": pid, "start": value}
                    self.baselines[key] = base
                data[key] = round(value - base["start"], 3)

        self._ratios_and_times(data)

    def _ratios_and_times(self, data: dict[str, Any]) -> None:
        """Self-consumption / self-sufficiency of today and battery time left."""
        pv, exp = data.get("pv_energy_daily"), data.get("grid_energy_export_daily")
        imp, house = data.get("grid_energy_import_daily"), data.get("house_energy_daily")
        data["self_consumption_daily"] = (
            None
            if pv is None or exp is None or pv <= 0
            else round(min(max((pv - exp) / pv * 100, 0), 100))
        )
        data["self_sufficiency_daily"] = (
            None
            if imp is None or house is None or house <= 0
            else round(min(max((1 - imp / house) * 100, 0), 100))
        )
        power, stored = data.get("battery_power"), data.get("battery_stored_energy")
        usable = data.get("battery_usable_energy")
        empty = full = None
        if power is not None and stored is not None and usable is not None:
            if power > IDLE_THRESHOLD_W:
                empty = round(usable / (power / 1000), 1)
            elif power < -IDLE_THRESHOLD_W:
                full = round(max(self.usable_capacity - stored, 0) / (-power / 1000), 1)
        data["battery_time_to_empty"] = empty
        data["battery_time_to_full"] = full

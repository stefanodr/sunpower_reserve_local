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

"""Sensors for SunPower Reserve Local."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SunPowerReserveCoordinator
from .registers import DERIVED, REGISTERS


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors."""
    coordinator: SunPowerReserveCoordinator = entry.runtime_data
    entities = [
        SunPowerReserveSensor(coordinator, entry, r.key, r.unit, r.device_class,
                              r.state_class, r.enabled, r.precision)
        for r in REGISTERS
    ]
    entities += [
        SunPowerReserveSensor(coordinator, entry, key, *spec)
        for key, spec in DERIVED.items()
    ]
    async_add_entities(entities)


class SunPowerReserveSensor(CoordinatorEntity[SunPowerReserveCoordinator], SensorEntity):
    """A value read from the inverter."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, unit, device_class, state_class,
                 enabled, precision) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = SensorDeviceClass(device_class) if device_class else None
        self._attr_state_class = SensorStateClass(state_class) if state_class else None
        self._attr_entity_registry_enabled_default = enabled
        self._attr_suggested_display_precision = precision
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="SunPower (AlphaESS)",
            model="Reserve inverter (Modbus TCP)",
            name="SunPower Reserve",
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self._key)

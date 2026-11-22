"""Sensors for SunPower Reserve Local."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SunPowerReserveCoordinator
from .energy import INTEGRATED, period_sensor_keys
from .registers import DERIVED, REGISTERS, STATE_SENSORS, TEXT_SENSORS

T = "total_increasing"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors."""
    coordinator: SunPowerReserveCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        SunPowerReserveSensor(coordinator, entry, r.key, r.unit, r.device_class,
                              r.state_class, r.enabled, r.precision, r.diagnostic)
        for r in REGISTERS
    ]
    entities += [
        SunPowerReserveSensor(coordinator, entry, key, *spec)
        for key, spec in DERIVED.items()
    ]
    entities += [
        SunPowerReserveSensor(coordinator, entry, key, "kWh", "energy", T, True, 2)
        for key in INTEGRATED.values()
    ]
    entities += [
        SunPowerReserveSensor(coordinator, entry, key, "kWh", "energy", T, enabled, 2)
        for key, enabled in period_sensor_keys()
    ]
    entities += [
        SunPowerReserveStateSensor(coordinator, entry, key, options)
        for key, options in STATE_SENSORS.items()
    ]
    entities += [
        SunPowerReserveTextSensor(coordinator, entry, key) for key in TEXT_SENSORS
    ]
    async_add_entities(entities)


def _device_info(entry: ConfigEntry, data: dict | None = None) -> DeviceInfo:
    data = data or {}
    return DeviceInfo(
        serial_number=data.get("serial_number"),
        sw_version=data.get("inverter_firmware"),
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="SunPower (AlphaESS)",
        model="Reserve inverter (Modbus TCP)",
        name="SunPower Reserve",
    )


class SunPowerReserveSensor(CoordinatorEntity[SunPowerReserveCoordinator], SensorEntity):
    """A numeric value read or derived from the inverter."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, unit, device_class, state_class,
                 enabled, precision, diagnostic=False) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = SensorDeviceClass(device_class) if device_class else None
        self._attr_state_class = SensorStateClass(state_class) if state_class else None
        self._attr_entity_registry_enabled_default = enabled
        self._attr_suggested_display_precision = precision
        if diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = _device_info(entry, coordinator.data)

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self._key)


class SunPowerReserveStateSensor(
    CoordinatorEntity[SunPowerReserveCoordinator], SensorEntity
):
    """A text state (charging, importing, ...)."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator, entry, key, options) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_options = options
        self._attr_device_info = _device_info(entry, coordinator.data)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get(self._key)


class SunPowerReserveTextSensor(CoordinatorEntity[SunPowerReserveCoordinator], SensorEntity):
    """A text value (firmware version)."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, key) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = _device_info(entry, coordinator.data)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get(self._key)

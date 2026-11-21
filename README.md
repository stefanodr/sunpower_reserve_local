# SunPower Reserve Local

[🇮🇹 Italiano](README.it.md)

Read-only, **fully local** Home Assistant integration for the SunPower Reserve
inverter/battery (an AlphaESS white label). It polls the inverter over
**Modbus TCP** on your LAN: no cloud, no account, no changes to dongle, DNS or router.

It complements the cloud integration `sunpower_maxeon` (which you still need for
battery control): this one only **reads**, it never writes. Only Modbus function code 3 is used.

## Requirements

- The inverter's **LAN port** connected to your network (cable to router / powerline). It gets its own IP (e.g. `192.168.1.45`), different from the Wi-Fi dongle.
- Modbus TCP on port `502`, unit ID `85` (defaults).
- The inverter accepts **one Modbus TCP connection at a time**: don't run other Modbus clients against it.

## Installation

### HACS (search)
1. HACS → search **SunPower Reserve Local** → Download.
2. Restart Home Assistant.

### HACS (custom repository)
1. HACS → ⋮ → Custom repositories → add `https://github.com/stefanodr/sunpower_reserve_local`, type *Integration*.
2. Download, then restart Home Assistant.

### Manual
Copy `custom_components/sunpower_reserve_local` into your `config/custom_components/` and restart.

## Setup

Settings → Devices & services → Add integration → **SunPower Reserve Local**, then enter
the inverter's IP (port 502, unit 85). Polling interval (default 15 s, min 10 s) is in the integration options.

## Sensors

Grid (import/export energy, power, voltage, frequency), battery (SOC, power, voltage, current,
charged/discharged energy), inverter (power, voltage), PV1/PV2 (V, A, W) and total PV power.
Sign convention: grid power negative = export; battery power/current negative = charging.

Sensors marked *experimental* (grid current, cell voltages, temperature, battery-from-grid energy,
max currents, L1 power, house load) are **disabled by default**: the register map was decoded by
observation and cross-checked with the cloud values (SOC, grid and battery energy totals match),
but those still need confirmation. Please compare with the app and report mismatches.

## Troubleshooting

- *Cannot read from the inverter*: check IP, that the LAN cable is connected, and that no other Modbus client is attached.
- Values frozen / unavailable: the inverter allows a single connection; stop other clients.

## Disclaimer
Unofficial, not affiliated with SunPower/Maxeon/AlphaESS. Use at your own risk.

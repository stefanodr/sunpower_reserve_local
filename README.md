# SunPower Reserve Local

[🇮🇹 Italiano](README.it.md)

Read-only, **fully local** Home Assistant integration for the SunPower Reserve
inverter/battery (an AlphaESS white label). It polls the inverter over
**Modbus TCP** on your LAN: no cloud, no account, no changes to dongle, DNS or router.

It complements the cloud integration `sunpower_maxeon` (which you still need for
battery control): this one only **reads**, it never writes. Only Modbus function code 3 is used.

## Requirements

- The inverter's **LAN port** connected to your network (cable to router / powerline). It gets its own IP (an address from your own network, e.g. `<inverter-ip>`), different from the Wi-Fi dongle. Find it in your router's device list (the LAN port usually appears as a "WIZnet" device).
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

- **Grid:** import/export energy, power, voltage, frequency, current, grid state.
- **Battery:** charge (SOC), power, voltage, current, charged/discharged energy, energy charged from grid, cell voltages, max charge/discharge current, stored energy, battery state.
- **Inverter:** power, voltage, temperature.
- **PV:** PV1/PV2 voltage, current and power, total PV power.
- **Diagnostics:** inverter, BMS and EMS firmware versions, export limit, installed PV power, inverter rated power (read at start-up and then hourly); the device also shows the serial number.
- **House:** house load (PV + battery + grid).
- **Energy totals and periods:** estimated PV and house energy totals (integrated from power) and daily, weekly, monthly and yearly counters for PV, house, grid import/export and battery charge/discharge.

Sign convention: grid power negative = export; battery power/current negative = charging.

PV and house energy have no readable register on the inverter, so they are integrated from power every poll. Totals and period starts are stored and survive restarts; periods start counting at the first run. In the integration options you can add an offset to the PV and house totals (for example to match the totals of another source) and set the battery usable capacity (default 9.576 kWh) used for the stored energy sensor.

Battery control (charge programme, export limit) is not available locally: keep the cloud integration for that.

## Troubleshooting

- *Cannot read from the inverter*: check IP, that the LAN cable is connected, and that no other Modbus client is attached.
- Values frozen / unavailable: the inverter allows a single connection; stop other clients.

## Disclaimer
Unofficial, not affiliated with SunPower/Maxeon/AlphaESS. Use at your own risk.

# SunPower Reserve Local

[🇮🇹 Italiano](README.it.md)

Read-only, **fully local** Home Assistant integration for the SunPower Reserve
inverter/battery (an AlphaESS white label). It polls the inverter over
**Modbus TCP** on your LAN: no cloud, no account, and no changes to the dongle, DNS or router.

## Read-only by design

The integration only ever sends Modbus **function code 3 (read holding registers)**. It has no code path
that writes to the inverter, so it cannot change settings or affect the warranty.

It complements the cloud integration [`sunpower_maxeon`](https://github.com/geims12/sunpower_maxeon),
which you still need for battery control (charge programme, export limit). The two can run side by side
because they talk to different endpoints.

## Requirements

- The inverter's **LAN port** connected to your network (cable to router / powerline). It gets its own IP address (an address from your own network, shown below as `<inverter-ip>`), different from the Wi-Fi dongle. Find it in your router's device list: the LAN port usually appears as a "WIZnet" device.
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
the inverter's IP (`<inverter-ip>`, port 502, unit 85).

### Options

| Option | Default | Meaning |
|---|---|---|
| Polling interval | 15 s (min 10 s) | How often the inverter is read |
| PV energy offset (kWh) | 0 | Added to the estimated PV energy total, e.g. to match another source |
| House energy offset (kWh) | 0 | Added to the estimated house energy total |
| Battery usable capacity (kWh) | 9.576 | Used for stored energy and battery time estimates |
| Backup reserve (% of charge) | 10 | Part of the charge kept for the backup line in a blackout: it cannot be discharged, so it is excluded from the usable energy and from the time to empty |

Offsets never affect the daily/weekly/monthly/yearly counters.

## Sensors

| Group | What you get |
|---|---|
| **Grid** | Import/export energy (totals), power, voltage, frequency, current, grid state |
| **Battery** | Charge (SOC), power, voltage, current, charged/discharged energy (totals), energy charged from grid, cell voltages, max charge/discharge current, stored energy, usable energy (without the backup reserve), battery state |
| **Inverter** | Power, L1 power, AC voltage, temperature |
| **PV** | PV1 and PV2 voltage, current and power, total PV power |
| **House** | House load (PV + battery + grid) |
| **Energy totals and periods** | Estimated PV and house energy totals, plus daily, weekly, monthly and yearly counters for PV, house, grid import/export and battery charge/discharge |
| **Dashboard helpers** | Battery charge/discharge power and grid import/export power as separate positive values, self-consumption and self-sufficiency of the day, battery time to empty / to full |
| **Diagnostics** | Inverter, BMS and EMS firmware versions, export limit, installed PV power, inverter rated power (read at start-up and then hourly); the device also shows the serial number |

Sign convention: grid power negative = export; battery power and current negative = charging.

### Good to know

- **PV and house energy are estimates.** The inverter has no readable register for them, so they are integrated from power at every poll. Grid and battery energy totals come straight from the inverter and match the cloud values.
- **Periods start counting at the first run.** Totals and period starts are stored and survive restarts, but "today", "this week", "this month" and "this year" are partial right after installation.
- **Some sensors are empty on purpose.** *Battery time to empty* is based on the usable energy (the backup reserve is excluded) and the current discharge power, so it changes quickly with the load. It only has a value while the battery discharges (above 20 W), and *time to full* only while it charges. Otherwise they are unknown.
- **Battery control is not available locally.** Use the cloud integration for the charge programme and the export limit.

## Troubleshooting

- *Cannot read from the inverter*: check the IP, that the LAN cable is connected, and that no other Modbus client is attached.
- Values frozen or unavailable: the inverter allows a single connection; stop other Modbus clients.
- Some values differ slightly from the cloud: the cloud updates much less often than this integration.

## Disclaimer
Unofficial, not affiliated with SunPower, Maxeon or AlphaESS. Use at your own risk.

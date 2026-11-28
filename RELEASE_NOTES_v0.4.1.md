## v0.4.1

### English
- New option: **backup reserve** (default 10 %). The battery keeps this part of the charge for the backup line in case of a blackout, so it cannot be discharged.
- New sensor: **battery usable energy** (kWh) = (charge − reserve) × capacity.
- Fixed: **battery time to empty** now uses the usable energy instead of the total stored energy, so it is no longer overestimated.
- Still strictly read-only (Modbus function code 3 only).

### Italiano
- Nuova opzione: **riserva backup** (predefinita 10 %). La batteria tiene questa parte di carica per la linea di backup in caso di blackout, quindi non può essere scaricata.
- Nuovo sensore: **energia utilizzabile in batteria** (kWh) = (carica − riserva) × capacità.
- Corretto: l'**autonomia della batteria** ora usa l'energia utilizzabile e non quella totale, quindi non è più sovrastimata.
- Sempre in sola lettura (solo funzione Modbus 3).

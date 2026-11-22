# Changelog

## 0.4.0 – 2026-11-22

### English
- New sensors for dashboards: battery charge/discharge power and grid import/export power as separate positive values.
- New: self-consumption and self-sufficiency of the day (%), battery time to empty and time to full (h).

### Italiano
- Nuovi sensori per le plance: potenza di carica/scarica della batteria e potenza prelevata/immessa in rete come valori separati e positivi.
- Novità: autoconsumo e autosufficienza del giorno (%), autonomia della batteria e tempo alla carica completa (ore).

## 0.3.0 – 2026-11-22

### English
- New diagnostic sensors read from the inverter: inverter, BMS and EMS firmware versions, export limit, installed PV power and inverter rated power (same values as the cloud integration).
- The device now shows the serial number and the inverter firmware version.
- Static information is read at start-up and then once an hour, so it adds no load to normal polling.

### Italiano
- Nuovi sensori diagnostici letti dall'inverter: versioni firmware di inverter, BMS ed EMS, limite di esportazione, potenza FV installata e potenza nominale dell'inverter (stessi valori dell'integrazione cloud).
- Il dispositivo ora mostra il numero di serie e la versione firmware dell'inverter.
- Le informazioni statiche vengono lette all'avvio e poi una volta l'ora, quindi non appesantiscono la lettura normale.

## 0.2.0 – 2026-11-22

### English
- New: estimated PV energy and house energy totals (integrated from power), plus daily, weekly, monthly and yearly counters for PV, house, grid import/export and battery charge/discharge.
- New: battery stored energy (kWh), battery state and grid state (charging/discharging/idle, importing/exporting/idle).
- New options: PV and house energy offsets (to align totals with another source such as the cloud) and battery usable capacity.
- All sensors are now enabled by default and no longer labelled experimental: values were verified against the cloud integration.
- Totals and period baselines are stored and survive restarts. Periods start counting from the first run.

### Italiano
- Novità: totali stimati di energia fotovoltaica e consumata (integrati dalla potenza), più contatori giornalieri, settimanali, mensili e annuali per FV, casa, prelievo/immissione in rete e carica/scarica batteria.
- Novità: energia immagazzinata in batteria (kWh), stato batteria e stato rete (carica/scarica/inattiva, prelievo/immissione/inattiva).
- Nuove opzioni: offset energia FV e casa (per allineare i totali a un'altra fonte, come il cloud) e capacità utilizzabile della batteria.
- Tutti i sensori sono ora abilitati di default e non più indicati come sperimentali: i valori sono stati verificati con l'integrazione cloud.
- Totali e punti di partenza dei periodi vengono salvati e restano dopo i riavvii. I periodi iniziano a contare dalla prima esecuzione.

## 0.1.2 – 2026-11-22

### English
- Fixed the "House load" sensor: it is now PV power + battery power + grid power (previously it used the inverter power register, which does not represent AC output). Verified against the cloud "instant consumption" value.

### Italiano
- Corretto il sensore "Consumo casa": ora è potenza FV + potenza batteria + potenza di rete (prima usava il registro della potenza inverter, che non rappresenta l'uscita AC). Verificato con il valore "consumo istantaneo" del cloud.

## 0.1.1 – 2026-11-21

### English
- Added integration icon (original artwork, in the `brand/` folder).
- Documentation and repository metadata fixes.

### Italiano
- Aggiunta l'icona dell'integrazione (grafica originale, nella cartella `brand/`).
- Correzioni a documentazione e metadati del repository.

## 0.1.0 – 2026-11-21

### English
- First release: read-only local Modbus TCP integration (function code 3 only).
- Grid, battery, inverter and PV sensors; experimental sensors disabled by default.
- Config flow (IP, port, unit ID) with connection check; polling interval option.

### Italiano
- Prima versione: integrazione locale Modbus TCP in sola lettura (solo funzione 3).
- Sensori rete, batteria, inverter e FV; sensori sperimentali disabilitati di default.
- Config flow (IP, porta, ID unità) con verifica connessione; opzione intervallo di lettura.

# Changelog

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

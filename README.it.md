# SunPower Reserve Local

[🇬🇧 English](README.md)

Integrazione Home Assistant **completamente locale** e in **sola lettura** per
inverter/batteria SunPower Reserve (rebrand AlphaESS). Legge l'inverter via
**Modbus TCP** sulla tua LAN: niente cloud, niente account, nessuna modifica a dongle, DNS o router.

Affianca l'integrazione cloud `sunpower_maxeon` (che serve ancora per il controllo della batteria):
questa **legge soltanto**, non scrive mai. Usa solo la funzione Modbus 3.

## Requisiti

- **Porta LAN dell'inverter** collegata alla rete (cavo al router / powerline). Ha un IP proprio (un indirizzo della tua rete, es. `<IP-inverter>`), diverso dal dongle Wi-Fi. Lo trovi nell'elenco dispositivi del router (la porta LAN di solito compare come dispositivo "WIZnet").
- Modbus TCP porta `502`, ID unità `85` (valori predefiniti).
- L'inverter accetta **una sola connessione Modbus TCP alla volta**: non usare altri client Modbus.

## Installazione

### HACS (ricerca)
1. HACS → cerca **SunPower Reserve Local** → Scarica.
2. Riavvia Home Assistant.

### HACS (repository personalizzato)
1. HACS → ⋮ → Repository personalizzati → aggiungi `https://github.com/stefanodr/sunpower_reserve_local`, tipo *Integrazione*.
2. Scarica e riavvia Home Assistant.

### Manuale
Copia `custom_components/sunpower_reserve_local` in `config/custom_components/` e riavvia.

## Configurazione

Impostazioni → Dispositivi e servizi → Aggiungi integrazione → **SunPower Reserve Local**,
poi inserisci l'IP dell'inverter (porta 502, unità 85). L'intervallo di lettura (predefinito 15 s, minimo 10 s) è nelle opzioni.

## Sensori

- **Rete:** energia prelevata/immessa, potenza, tensione, frequenza, corrente, stato rete.
- **Batteria:** carica (SOC), potenza, tensione, corrente, energia caricata/scaricata, energia caricata da rete, tensioni celle, correnti massime di carica/scarica, energia immagazzinata, stato batteria.
- **Inverter:** potenza, tensione, temperatura.
- **Fotovoltaico:** tensione, corrente e potenza di PV1/PV2, potenza FV totale.
- **Casa:** consumo casa (FV + batteria + rete).
- **Totali energia e periodi:** totali stimati di energia FV e consumata (integrati dalla potenza) e contatori giornalieri, settimanali, mensili e annuali per FV, casa, prelievo/immissione in rete e carica/scarica batteria.

Segni: potenza di rete negativa = immissione; potenza/corrente batteria negative = carica.

L'energia FV e quella consumata non hanno un registro leggibile sull'inverter, quindi vengono integrate dalla potenza a ogni lettura. Totali e inizio dei periodi vengono salvati e restano dopo i riavvii; i periodi iniziano a contare dalla prima esecuzione. Nelle opzioni puoi aggiungere un offset ai totali FV e casa (ad esempio per allinearli a un'altra fonte) e impostare la capacità utilizzabile della batteria (predefinita 9,576 kWh) usata dal sensore di energia immagazzinata.

Il controllo della batteria (programma di carica, limite di esportazione) non è disponibile in locale: per quello tieni l'integrazione cloud.

## Risoluzione problemi

- *Impossibile leggere dall'inverter*: controlla IP, cavo LAN collegato e che nessun altro client Modbus sia connesso.
- Valori fermi / non disponibili: l'inverter ammette una sola connessione; ferma gli altri client.

## Avvertenza
Non ufficiale, non affiliata a SunPower/Maxeon/AlphaESS. Uso a proprio rischio.

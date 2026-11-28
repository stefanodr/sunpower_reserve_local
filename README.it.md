# SunPower Reserve Local

[🇬🇧 English](README.md)

Integrazione Home Assistant **completamente locale** e in **sola lettura** per
inverter/batteria SunPower Reserve (rebrand AlphaESS). Legge l'inverter via
**Modbus TCP** sulla tua LAN: niente cloud, niente account e nessuna modifica a dongle, DNS o router.

## Sola lettura per progetto

L'integrazione invia soltanto la **funzione Modbus 3 (lettura dei registri)**. Non esiste nessun percorso
di codice che scriva sull'inverter, quindi non può modificare impostazioni né influire sulla garanzia.

Affianca l'integrazione cloud [`sunpower_maxeon`](https://github.com/geims12/sunpower_maxeon),
che serve ancora per il controllo della batteria (programma di carica, limite di esportazione). Le due possono
funzionare insieme perché parlano con punti diversi.

## Requisiti

- **Porta LAN dell'inverter** collegata alla rete (cavo al router / powerline). Ha un indirizzo IP proprio (un indirizzo della tua rete, indicato sotto come `<IP-inverter>`), diverso dal dongle Wi-Fi. Lo trovi nell'elenco dispositivi del router: la porta LAN di solito compare come dispositivo "WIZnet".
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
poi inserisci l'IP dell'inverter (`<IP-inverter>`, porta 502, unità 85).

### Opzioni

| Opzione | Predefinito | Significato |
|---|---|---|
| Intervallo di lettura | 15 s (min 10 s) | Ogni quanto viene letto l'inverter |
| Offset energia FV (kWh) | 0 | Si somma al totale stimato dell'energia FV, ad esempio per allinearlo a un'altra fonte |
| Offset energia casa (kWh) | 0 | Si somma al totale stimato dell'energia consumata |
| Capacità utilizzabile batteria (kWh) | 9,576 | Usata per l'energia immagazzinata e per le stime di tempo della batteria |
| Riserva backup (% di carica) | 10 | Parte di carica tenuta per la linea di backup in caso di blackout: non si può scaricare, quindi è esclusa dall'energia utilizzabile e dall'autonomia |

Gli offset non influiscono sui contatori giornalieri, settimanali, mensili e annuali.

## Sensori

| Gruppo | Cosa ottieni |
|---|---|
| **Rete** | Energia prelevata/immessa (totali), potenza, tensione, frequenza, corrente, stato rete |
| **Batteria** | Carica (SOC), potenza, tensione, corrente, energia caricata/scaricata (totali), energia caricata da rete, tensioni celle, correnti massime di carica/scarica, energia immagazzinata, energia utilizzabile (senza la riserva backup), stato batteria |
| **Inverter** | Potenza, potenza L1, tensione AC, temperatura |
| **Fotovoltaico** | Tensione, corrente e potenza di PV1 e PV2, potenza FV totale |
| **Casa** | Consumo casa (FV + batteria + rete) |
| **Totali energia e periodi** | Totali stimati di energia FV e consumata, più contatori giornalieri, settimanali, mensili e annuali per FV, casa, prelievo/immissione in rete e carica/scarica batteria |
| **Per le plance** | Potenza di carica/scarica batteria e potenza prelevata/immessa in rete come valori positivi separati, autoconsumo e autosufficienza del giorno, autonomia batteria e tempo alla carica completa |
| **Diagnostica** | Versioni firmware di inverter, BMS ed EMS, limite di esportazione, potenza FV installata, potenza nominale inverter (lette all'avvio e poi ogni ora); il dispositivo mostra anche il numero di serie |

Segni: potenza di rete negativa = immissione; potenza e corrente della batteria negative = carica.

### Da sapere

- **Energia FV e consumata sono stime.** L'inverter non ha un registro leggibile per queste due, quindi vengono integrate dalla potenza a ogni lettura. I totali di rete e batteria arrivano direttamente dall'inverter e coincidono con quelli del cloud.
- **I periodi iniziano a contare dalla prima esecuzione.** Totali e partenze dei periodi vengono salvati e restano dopo i riavvii, ma "oggi", "settimana", "mese" e "anno" sono parziali subito dopo l'installazione.
- **Alcuni sensori sono vuoti di proposito.** *Autonomia batteria* si basa sull'energia utilizzabile (la riserva backup è esclusa) e sulla potenza di scarica del momento, quindi cambia rapidamente con il carico. Ha un valore solo mentre la batteria si scarica (sopra 20 W), e *tempo alla carica completa* solo mentre si carica. Altrimenti sono sconosciuti.
- **Il controllo della batteria non è disponibile in locale.** Per il programma di carica e il limite di esportazione usa l'integrazione cloud.

## Risoluzione problemi

- *Impossibile leggere dall'inverter*: controlla IP, cavo LAN collegato e che nessun altro client Modbus sia connesso.
- Valori fermi o non disponibili: l'inverter ammette una sola connessione; ferma gli altri client Modbus.
- Alcuni valori differiscono di poco dal cloud: il cloud si aggiorna molto meno spesso di questa integrazione.

## Avvertenza
Non ufficiale, non affiliata a SunPower, Maxeon o AlphaESS. Uso a proprio rischio.

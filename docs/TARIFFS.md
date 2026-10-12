# Prezzi della componente energia

L'integrazione espone tre sensori per ogni fornitura presente nell'account,
anche quando mancano i consumi. Account con la sola luce, il solo gas o entrambe
le forniture seguono lo stesso flusso e non dipendono dalla presenza dell'altra
commodity:

| Sensore | Unità | Significato |
| :--- | :--- | :--- |
| Verifica tariffa | stato | Spiega se e perché le condizioni economiche sono disponibili. |
| Prezzo componente energia | EUR/kWh luce, EUR/Smc gas | Corrispettivo per il consumo nelle condizioni economiche verificate. |
| Quota fissa annua vendita | EUR/year | Corrispettivo annuo del venditore, distinto dal prezzo unitario. |

Sono valori delle condizioni economiche pubbliche abbinate all'offerta, non
importi estratti dalla propria fattura. Il prezzo unitario esclude la quota
fissa, IVA, accise, trasporto, oneri di sistema e gli altri corrispettivi.
Per la luce restano esclusi anche dispacciamento e mercato della capacità.
L'attributo `network_losses_included` compare soltanto quando la fonte consente
di verificare se le perdite di rete sono comprese; non viene dedotto dal nome
dell'offerta.
La quota annua non è l'importo della prossima bolletta.

Per il gas, quando disponibile, `reference_pcs_gj_smc` indica il PCS standard
riportato nel documento. Se la fonte open data non lo specifica, l'attributo
resta assente. Il prezzo effettivamente applicato può essere adeguato al PCS
del luogo di fornitura. Gli **Smc** sono metri cubi standard: non sostituire
questa unità con i m³ letti al contatore, che richiedono il coefficiente C.
L'integrazione non effettua queste conversioni e non calcola il costo completo
della bolletta. I sensori sono utilizzabili nelle proprie automazioni; non
configurano automaticamente il calcolo dei costi nella dashboard Energy.

## Catalogo verificato

Il catalogo incluso nel componente contiene **203 codici verificati**: 98 con
entrambe le commodity, 104 con il solo gas e uno con la sola luce, per un totale
di 301 tariffe indipendenti. La copertura deriva dagli open data ufficiali del
Portale Offerte campionati dal luglio 2022 all'11 ottobre 2026; la prima offerta
compatibile rinvenuta decorre da ottobre 2023. Il componente non interroga il
Portale Offerte durante il polling e non richiede prezzi inseriti manualmente.

Le 19 versioni seguenti di Energia PuntoFisso Mono 12 mesi hanno anche una
verifica aggiuntiva sulle CTE pubbliche ENGIE. Non sono diciannove famiglie
commerciali diverse. I dati CTE hanno precedenza sul corrispondente record open
data perché documentano anche perdite di rete e PCS:

| Codice completo | Luce EUR/kWh | Luce EUR/anno | Gas EUR/Smc | Gas EUR/anno | Fonte |
| :--- | ---: | ---: | ---: | ---: | :--- |
| PUMD#00008 | 0,11620 | 72,00 | 0,48400 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00008) |
| PUMD#00009 | 0,11620 | 72,00 | 0,47600 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00009) |
| PUMD#00010 | 0,11675 | 72,00 | 0,48300 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00010) |
| PUMD#00011 | 0,12290 | 72,00 | 0,48300 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00011) |
| PUMD#00012 | 0,12290 | 72,00 | 0,48300 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00012) |
| PUMD#00013 | 0,11860 | 72,00 | 0,48300 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00013) |
| PUMD#00014 | 0,11860 | 72,00 | 0,48300 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00014) |
| PUMD#00015 | 0,11860 | 72,00 | 0,46450 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00015) |
| PUMD#00016 | 0,11670 | 72,00 | 0,45450 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00016) |
| PUMD#00017 | 0,11340 | 72,00 | 0,45450 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00017) |
| PUMD#00018 | 0,12051 | 72,00 | 0,53900 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00018) |
| PUMD#00020 | 0,12865 | 72,00 | 0,55450 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00020) |
| PUMD#00021 | 0,13500 | 72,00 | 0,55450 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00021) |
| PUMD#00022 | 0,14090 | 72,00 | 0,59900 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00022) |
| PUMD#00023 | 0,14090 | 72,00 | 0,69000 | 84,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00023) |
| PUMD#00024 | 0,18400 | 120,00 | 0,75000 | 120,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00024) |
| PUMD#00025 | 0,19900 | 120,00 | 0,89000 | 120,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00025) |
| PUMD#00026 | 0,19900 | 108,00 | 0,92000 | 108,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00026) |
| PUMD#00027 | 0,19900 | 108,00 | 0,92000 | 108,00 | [CTE ENGIE](https://www.engie.it/documents/d/casa/223_pumd-00027) |

Documenti CTE controllati fino all'11 ottobre 2026, con confronto delle
condizioni e verifica visiva delle tabelle della componente energia e delle
quote annue.
I documenti condividono durata di dodici mesi, perdite luce incluse, assenza di
sconti e PCS gas di riferimento 0,03852 GJ/Smc. Ogni versione ha i propri prezzi
e la propria finestra di sottoscrizione: non viene usato il prezzo dell'ultima
offerta disponibile come valore di ripiego.

URL, finestre di sottoscrizione e impronte SHA-256 dei PDF esaminati sono nel
[registro delle fonti](TARIFF_SOURCES.md). Il catalogo JSON contiene anche la
fonte open data di ogni altra tariffa. La scadenza per sottoscrivere l'offerta
è distinta dalla validità economica del contratto: la durata verificata decorre
dall'attivazione della prima fornitura. Il prezzo già supportato per
`PUMD#00016` resta invariato.

L'abbinamento usa `prodottoCodiceUnivoco` e `productCode` della risposta
forniture; il nome commerciale non viene usato. Ogni codice può contenere una
tariffa luce, una tariffa gas o entrambe. La presenza di una commodity non
autorizza mai a dedurre il prezzo dell'altra. L'abbinamento richiede prezzo
`FIXED`, uso domestico riconosciuto e un periodo `inizioCE`–`fineCE` coerente
con la durata verificata nel catalogo e con la prima attivazione del contratto.
Attualmente le tipologie osservate
sono `Domestico residente` per la luce e `A – Uso Domestico` per il gas.
Altre tipologie, comprese quelle domestiche non ancora verificate, rimangono
indisponibili. Con attivazioni duali distinte, la seconda fornitura attende
la propria attivazione ma mantiene la scadenza comune.

**Il rinnovo o il cambio prodotto non riutilizzano automaticamente il prezzo
iniziale.** Non sono ancora supportati prezzi indicizzati, fasce orarie,
versioni non presenti nel catalogo o condizioni personalizzate non verificabili.
Eventuali accordi individuali e successive comunicazioni contrattuali devono
essere verificati nelle proprie condizioni e fatture.

## Disponibilità e attributi

Il sensore **Verifica tariffa** rende leggibile il risultato direttamente nella
pagina del dispositivo. Fonte `source_url`, codice `offer_code`, date
`valid_from` e `valid_until`, `price_type`, `duration_months` e limiti del
prezzo sono anche negli attributi.
Gli importi diventano indisponibili, senza ripiego a zero, se l'abbinamento non
è verificabile. Lo stato ne indica il motivo:

| Stato | Significato |
| :--- | :--- |
| verified | Condizioni pubbliche abbinate e attualmente valide. |
| missing_metadata | Dati offerta assenti, incompleti o malformati. |
| unverified_offer | Codice/versione non presente nel catalogo verificato. |
| unverified_commodity | Il codice è noto, ma la variante luce o gas della fornitura non è verificata. |
| unsupported_terms | Tipo di contratto, prezzo, durata o date non supportati. |
| unverified_renewal | Decorrenza economica diversa dalla prima attivazione. |
| not_yet_valid | Decorrenza o attivazione non ancora raggiunta. |
| expired | Periodo economico terminato. |
| inactive | Fornitura non confermata attiva. |
| update_failed | Aggiornamento dell'account non riuscito. |

La validità è ricontrollata a mezzanotte italiana anche fra due aggiornamenti,
senza chiamate API aggiuntive. I prezzi non dipendono dalla disponibilità di
consumi o fatture; un errore nel recupero delle forniture li rende indisponibili.
Gli identificativi delle entità restano stabili al cambio d'offerta.
La diagnostica esportata non include codici offerta, date economiche o prezzi.

## Catalogo JSON e aggiornamenti

I dati risiedono in
[`api/data/tariffs.json`](../custom_components/engie_italia/api/data/tariffs.json).
È il catalogo usato dal componente e dal client Python: una voce per ogni
codice completo. All'interno sono presenti `electricity`, `gas` oppure entrambe,
ciascuna con il proprio prezzo, quota annua, unità, durata, finestra di
sottoscrizione, URL e SHA-256 della fonte pubblica. Almeno una commodity è
obbligatoria; una voce vuota non è valida.

`schema_version` identifica il formato del file; la versione corrente è `2` e
`offers` contiene le offerte.
Gli importi vanno scritti come **stringhe decimali con il punto**, per esempio
`"0.11670"` e `"72.00"`, per conservarne la precisione. Le date usano
`YYYY-MM-DD`. Non aggiungere campi arbitrari o duplicare codici.

Per aggiungere una versione con condizioni già supportate è sufficiente
aggiornare il JSON e la documentazione delle fonti. Nuove famiglie, fasce,
durate o regole contrattuali richiedono anche una verifica della logica:
inserire un codice nel file non rende supportate condizioni diverse.

Il catalogo è incluso nella release, letto localmente una sola volta e
aggiornato insieme all'integrazione tramite HACS, con riavvio di Home Assistant.
Non è un database remoto e non scarica nuove tariffe da Internet.

Gli open data giornalieri del Portale Offerte ARERA sono una fonte utile per
ricostruire le offerte rivolte alla generalità dei clienti. Non comprendono
necessariamente rinnovi, condizioni personalizzate o proposte riservate; per
questo una versione osservata nell'account non viene considerata verificata
soltanto perché esiste una versione vicina nello storico pubblico.
Le modifiche manuali nella cartella installata vengono sostituite al prossimo
aggiornamento: proporle nel repository per distribuirle a tutti.

Lo strumento [`tools/import_portale_offerte.py`](../tools/import_portale_offerte.py)
costruisce un inventario ripetibile degli snapshot ufficiali. Importa soltanto
record domestici a prezzo fisso che il modello attuale può rappresentare senza
perdere fasce, scaglioni, periodi o sconti. Luce e gas vengono analizzati e
salvati separatamente; prezzi indicizzati, multiorari o ambigui restano
nell'inventario con il motivo dell'esclusione.

Per le fonti PDF, `source_sha256` identifica l'intero documento. Per gli open
data identifica invece l'esatto elemento XML `<offerta>` estratto dallo snapshot
indicato da `source_url`; in questo modo la prova resta stabile senza incorporare
nel pacchetto file giornalieri di molti megabyte.

## Aggiungere altre versioni

Aprire una issue con il collegamento al documento **pubblico** ENGIE. Verificare
codice completo, uso domestico, durata, componente energia, perdite, PCS,
quote fisse, sconti e regole di rinnovo prima di ampliare `api/data/tariffs.json`.
Aggiornare la tabella sopra e il [registro delle fonti](TARIFF_SOURCES.md).
La somiglianza del nome o del percorso URL non è una verifica.
Non allegare contratti personali, fatture, POD/PDR, token o risposte dell'account.
I test devono usare offerte, prezzi e account interamente sintetici.

Dopo l'installazione dell'ambiente di sviluppo (`pip install -e ".[dev]"`),
verificare il catalogo incluso:

```sh
python -m engie_italia.tariff_catalog
```

Per controllare un file proposto senza installarlo:

```sh
python -m engie_italia.tariff_catalog percorso/tariffs.json
```

Il comando termina con errore per JSON malformato, campi mancanti o inattesi,
codici duplicati, formato non supportato, date incoerenti, prezzi ambigui,
unità errate o riferimenti incompleti. Controlla la struttura: la correttezza
dei valori rispetto al PDF richiede sempre la revisione della fonte.
La CI verifica anche il catalogo contenuto nel pacchetto Python distribuito.

Se il file installato manca o non è valido, il componente registra un errore
e lascia indisponibili i sensori tariffari; forniture, consumi e fatture
continuano a funzionare secondo la disponibilità del servizio. Nessun prezzo
parziale o valore di ripiego viene usato. Riscaricare la release corretta e
riavviare Home Assistant ripristina il catalogo incluso.

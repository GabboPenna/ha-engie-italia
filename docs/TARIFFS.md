# Prezzi della componente energia

La b10 aggiunge due sensori per ogni fornitura, anche quando mancano i consumi:

| Sensore | Unità | Significato |
| :--- | :--- | :--- |
| Prezzo componente energia | EUR/kWh luce, EUR/Smc gas | Corrispettivo per il consumo nelle condizioni economiche verificate. |
| Quota fissa annua vendita | EUR/year | Corrispettivo annuo del venditore, distinto dal prezzo unitario. |

Sono valori delle condizioni economiche pubbliche abbinate all'offerta, non
importi estratti dalla propria fattura. Il prezzo unitario esclude la quota
fissa, IVA, accise, trasporto, oneri di sistema e gli altri corrispettivi.
Per la luce restano esclusi anche dispacciamento e mercato della capacità;
le perdite di rete sono già comprese nella componente energia qui supportata.
La quota annua non è l'importo della prossima bolletta.

Per il gas il prezzo è riferito al PCS standard indicato nel documento
(`reference_pcs_gj_smc`). Il prezzo effettivamente applicato può essere adeguato
al PCS del luogo di fornitura. Gli **Smc** sono metri cubi standard: non sostituire
questa unità con i m³ letti al contatore, che richiedono il coefficiente C.
L'integrazione non effettua queste conversioni e non calcola il costo completo
della bolletta. I sensori sono utilizzabili nelle proprie automazioni; non
configurano automaticamente il calcolo dei costi nella dashboard Energy.

## Copertura iniziale

Il catalogo incluso nel componente contiene soltanto versioni controllate sui
documenti pubblici ENGIE. Non scarica o interpreta PDF a ogni aggiornamento e
non richiede un prezzo inserito manualmente.

| Codice completo | Luce EUR/kWh | Luce EUR/anno | Gas EUR/Smc | Gas EUR/anno | Fonte |
| :--- | ---: | ---: | ---: | ---: | :--- |
| PUMD#00016 | 0,11670 | 72,00 | 0,45450 | 84,00 | [CTE ENGIE, pagine 1–3](https://www.engie.it/documents/d/casa/223_pumd-00016) |

Documento controllato il 16 settembre 2026; PCS gas di riferimento
0,03852 GJ/Smc. SHA-256 del PDF esaminato:
`d9342c1e1c7a6813294cef34017928c47442e005b1ef6131443144f4dcc843e5`.
La finestra di sottoscrizione 9–15 luglio 2026 è distinta dai dodici mesi di
applicazione, che decorrono dall'attivazione della prima fornitura.

L'abbinamento usa `prodottoCodiceUnivoco` e `productCode` della risposta
forniture; il nome commerciale non viene usato. Richiede prezzo `FIXED`, uso
domestico riconosciuto e un periodo `inizioCE`–`fineCE` coerente con `durataCE=12`
e con la prima attivazione del contratto. Attualmente le tipologie osservate
sono `Domestico residente` per la luce e `A – Uso Domestico` per il gas.
Altre tipologie, comprese quelle domestiche non ancora verificate, rimangono
indisponibili. Con attivazioni duali distinte, la seconda fornitura attende
la propria attivazione ma mantiene la scadenza comune.

**Il rinnovo o il cambio prodotto non riutilizzano automaticamente il prezzo
iniziale.** Non sono ancora supportati prezzi indicizzati, fasce orarie,
altre versioni della stessa offerta o condizioni personalizzate non verificabili.
Eventuali accordi individuali e successive comunicazioni contrattuali devono
essere verificati nelle proprie condizioni e fatture.

## Disponibilità e attributi

Fonte `source_url`, codice `offer_code`, date `valid_from` e `valid_until` e
limiti del prezzo sono negli attributi. Gli importi diventano indisponibili,
senza ripiego a zero, se l'abbinamento non è verificabile. `tariff_status`
ne indica il motivo:

| Stato | Significato |
| :--- | :--- |
| verified | Condizioni pubbliche abbinate e attualmente valide. |
| missing_metadata | Dati offerta assenti, incompleti o malformati. |
| unverified_offer | Codice/versione non presente nel catalogo verificato. |
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

## Aggiungere altre versioni

Aprire una issue con il collegamento al documento **pubblico** ENGIE. Verificare
codice completo, uso domestico, durata, componente energia, perdite, PCS,
quote fisse, sconti e regole di rinnovo prima di ampliare il catalogo in
`api/tariffs.py`. La somiglianza del nome o del percorso URL non è una verifica.
Non allegare contratti personali, fatture, POD/PDR, token o risposte dell'account.
I test devono usare offerte, prezzi e account interamente sintetici.

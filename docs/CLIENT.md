# Client e autenticazione

`EngieMobileClient` usa una `aiohttp.ClientSession` fornita dal chiamante.
Il chiamante resta responsabile della chiusura della sessione. Le richieste
usano TLS verificato, un timeout di 20 secondi e risposte limitate a 4 MiB.
Non configurare trace HTTP che esportino header, URL completi o payload.

## Operazioni disponibili

- `async_supplies()`: forniture luce/gas senza anagrafica e dati di pagamento.
- `async_invoices()`: riepilogo fatture dei contratti dell'account, sperimentale;
  restituisce `InvoiceSnapshot` con documenti normalizzati e data di lettura.
- `async_commissioning_date(supply)`: data di disponibilita' del servizio elettrico.
- `lower_bound(supply, commissioning_date, today=...)`: limite iniziale osservato
  nell'app, basato su commissioning/attivazione e un massimo di due anni indietro.
- `async_daily_electricity(supply, lower_bound=..., year=...)`: un anno alla volta.
- `async_hourly_electricity(supply, lower_bound=..., day=...)`: un giorno alla volta.
- `async_refresh()`: rinnovo esplicito della sessione gia' autorizzata.
- `clear_credentials()`: elimina i riferimenti alle credenziali dal client;
  non revoca il consenso presso il provider e non garantisce azzeramento della RAM.

La lettura dei consumi gas non e' esposta finche' non e' disponibile uno schema
di successo verificato. Il parser riconosce la fornitura gas, non inventa misure.
Il client non effettua richieste periodiche in autonomia e non contiene funzioni
di pagamento, autolettura, profilo o modifica contrattuale.

`async_invoices()` carica i contratti con `async_supplies()` se non sono già
disponibili. Aggiornare le forniture prima di ogni ciclo per rilevare cambi di
contratto, come fa il coordinatore HA. Una sola richiesta per codice contratto,
senza limite al numero delle fatture. Non restituisce riepiloghi parziali se
una richiesta fallisce. Codici `engieErrorCode`/`engieDetailedErrorCode` diversi
da zero vengono rifiutati anche con HTTP 200 e `code: OK`.

## Credenziali e recupero

Il costruttore richiede `api_key` e `access_token`. Per il rinnovo richiede anche
`client_id` e `refresh_token`; `expires_in` puo' indicare la validita' residua.
Questi valori non devono comparire in codice, issue, log, comandi shell o commit.
Non viene richiesto di inserire password nel client Python.

Il config flow usa OAuth Authorization Code con PKCE S256, state/nonce e
validazione dell'ID token RS256 tramite le chiavi dell'issuer. Login ed eventuale
challenge rimangono nel browser ENGIE. `auth.py` verifica un callback esatto,
con tentativo a uso singolo e scadenza di 10 minuti. I tool browser di ricerca
esistenti riguardano invece il portale web e non configurano la sessione HA.

Le richieste di lettura sono serializzate per account. Quelle contemporanee
con lo stesso percorso e gli stessi parametri condividono una sola operazione
HTTP, compreso l'eventuale rinnovo. Account e parametri diversi restano separati.
Annullare un chiamante non interrompe gli altri; quando tutti annullano la
richiesta, o vengono eliminate le credenziali, la lettura in corso viene annullata.
Un 401 causa al massimo
un rinnovo e una ripetizione; un secondo rifiuto richiede login interattivo.
Token prossimi alla scadenza vengono rinnovati prima della lettura. Un rinnovo
malformato non provoca il riutilizzo continuo di un possibile token gia' ruotato.

Il callback opzionale `token_updated(SessionTokens)` viene atteso dopo ogni
rinnovo e prima di ulteriori letture. HA lo collega al deposito privato atomico.
Un salvataggio fallito causa `TokenPersistenceError`; il token nuovo rimane in
memoria e il salvataggio viene ritentato prima della successiva richiesta.
`SessionTokens` include scadenza assoluta e serializzazione esplicitamente privata
per riprendere la sessione dopo un riavvio. Senza callback il client resta in RAM.
Il config flow HA usa il profilo applicativo comune incluso in `api/app.py`.
Il client resta parametrico per test e riautenticazione di account esistenti.
Le condizioni d'uso e distribuzione restano da verificare per l'uso generalizzato.

I 429 rispettano `Retry-After` e bloccano altre richieste fino alla scadenza,
senza attese occupate o login ripetuti. Rete/5xx non vengono riprovati in ciclo;
il coordinatore HA usa 6 ore di default e il recupero standard di HA. Gli errori
di una fornitura non bloccano le altre: i vecchi dati possono restare in memoria,
ma i relativi sensori diventano indisponibili fino al recupero.
Anche gli errori delle fatture sono isolati dai consumi; errori di autenticazione
o persistenza della sessione continuano a propagarsi all'intero coordinatore.

## Significato dei dati

`ElectricityReadings.snapshot.intervals` contiene esclusivamente i campioni
alla granularita' richiesta. `year_totals`, `month_totals` e `day_total` sono
riepiloghi indipendenti forniti da ENGIE. **Non sommarli ai campioni.** I totali
possono differire dalla somma dei dettagli arrotondati: non vengono ricalcolati.

`last_update` e' la data comunicata da ENGIE, distinta da `fetched_at`.
Non e' una misura in tempo reale e non sostituisce l'inverter o il contatore locale.
`REAL`, `ESTIMATED` e `NOT_PROVIDED` sono distinti; quest'ultimo produce `None`,
anche se il payload include uno zero segnaposto. Uno zero reale resta zero.

I periodi sono interpretati in `Europe/Rome`. I giorni possono durare 23 o 25 ore.
Il formato orario osservato non include un offset: un'ora ripetuta al cambio
autunnale viene rifiutata come ambigua, non attribuita arbitrariamente a un fuso.
Un'ora inesistente viene rifiutata. Serie sparse rimangono sparse; duplicati,
periodi incoerenti e valori non finiti/negativi sono errori.

Nessuna importazione automatica nella dashboard Energy in questa fase:
rettifiche, arrotondamenti e doppio conteggio con misure locali vanno gestiti prima.

### Cache e rettifiche della situazione corrente

Dalla b9 la deduplicazione dura soltanto finché la lettura è condivisa da
chiamanti contemporanei. Risultati ed errori non vengono memorizzati per le
richieste successive: il normale aggiornamento e il pulsante manuale rileggono
consumi e fatture. Una risposta corretta sostituisce interamente la precedente,
anche se `lastUpdate` è identico o un totale diminuisce. Non si accumulano
differenze e non si riempiono campioni che ENGIE ha rimosso.

Il coordinatore conserva la commissioning date per il giorno locale e per
la combinazione POD, contratto e data di attivazione. Un cambio di contratto
o attivazione invalida la cache; le forniture rimosse vengono eliminate dalla
cache. Gli identificativi dei sensori restano legati al punto di fornitura.

Questa politica copre i riepiloghi correnti. L'eventuale importazione e
rettifica retroattiva delle statistiche Energy resta un lavoro separato.

`InvoiceSnapshot` usa il numero fiscale per distinguere i documenti; conserva
solo importo, residuo, emissione, scadenza e stato di pagamento. Importi in EUR
come `Decimal`, date di calendario e nessun PDF/URL o dato bancario. Il totale
aperto somma esclusivamente i residui confermati. Campi incompleti danno `None`,
non zero. Schema verificato staticamente, risposta positiva con fatture reali
ancora da confermare: [semantica e limiti](INVOICES.md).

# Ricerca API

## Osservazioni pubbliche, 16 settembre 2026

Il sito ufficiale collega lo Spazio Clienti a
`https://4you.engie.it/spazioclienti/ACMAAuthentication`.
Da un browser nuovo sono state osservate richieste Salesforce Aura,
fra cui `/spazioclienti/aura`. Premendo Accedi si raggiunge
`https://login.engie.it/u/login/identifier`, con un campo email.

Quella prima verifica non comprendeva credenziali o forniture. Il percorso
pubblico non dimostra la disponibilita' di API consumi o di un rinnovo
sessione utilizzabile da un'integrazione. Lo strumento `inspect_portal.py`
rimane limitato alla navigazione al login.

Nella ricerca preliminare non e' stata trovata documentazione pubblica
delle API consumer italiane. Le integrazioni ENGIE per altri Paesi non
dimostrano compatibilita' con l'account italiano.

L'app italiana dichiara consultazione di consumi luce/gas, contratti,
bollette e autolettura gas. Le funzioni dell'app non garantiscono che
gli stessi dati siano accessibili dal portale web o con la stessa API.

Fonti:
- [Spazio Clienti ENGIE](https://www.engie.it/casa/per-te/spazio-clienti/)
- [App ufficiale](https://play.google.com/store/apps/details?id=it.engie.appengie)
- [Portale pubblico](https://4you.engie.it/spazioclienti/ACMAAuthentication)

## Verifica autenticata, 16 settembre 2026

Accesso manuale completato dall'intestatario in un browser temporaneo.
Nessuna password o OTP acquisiti dal progetto e nessuna sessione esportata.
La verifica e' stata svolta in sola consultazione; nessuna operazione esplicita
di pagamento, invio autoletture, modifica contrattuale o anagrafica.

### Forniture verificate

La pagina autenticata `/spazioclienti/ACMADashboard` inizializza
`window.__data__` e lo passa al componente Salesforce `c:ACMARoot`.
Il cambio di scheda Forniture non richiede necessariamente una nuova chiamata
di elenco: i dati sono gia' nel caricamento iniziale.

Struttura verificata e utilizzata dal parser:

```text
contractChains: mappa con chiavi private
  <catena>: oggetto
    forniture: lista
      id: stringa privata
      commodity: "Luce" oppure "Gas"
      statoCalc: "attiva" osservato; altri valori restano sconosciuti
```

Il parser `engie_italia.portal.parse_dashboard_supplies` e la lettura di
`tools/probe_account.py` sono stati eseguiti sulla sessione reale.
Gli identificativi rimangono privati e non compaiono nel riepilogo o nella
rappresentazione dei modelli. La loro stabilita' al rinnovo contrattuale
non e' ancora verificata: non sono una scelta definitiva per gli unique ID HA.

Il bootstrap contiene anche metadati bollette in `bills.data`, oltre a dati
personali e di pagamento non necessari. Il parser li scarta. Non sono stati
implementati nel parser del portale download documenti, importi/scadenze o interpretazioni dei campi
`consumoE`, `consumoG`, `perFat` e dei valori del contatore.
La presenza di questi campi non ne dimostra unita', periodo o granularita'.

Lo script esterno inizializza un oggetto JavaScript, non JSON puro: non usare
`eval` o sostituzioni testuali per trasformarlo in un futuro client HTTP.
La prova attuale legge l'oggetto gia' decodificato dal browser del portale.

### Storico non utilizzabile nella prova

Nei bundle del portale e' presente l'operazione di lettura
`apex://ACMATendrilCnt/ACTION$HistoricalConsumption_get`, invocata via POST
su `/spazioclienti/aura`. Il chiamante usa `USERID`, `CONTRACT_LIST` e il
canale del portale `SOURCE_CHANNEL=ACMAWEB`, con contesto/sessione Aura.
Non sono API documentate pubblicamente ne' un contratto stabile.

Una prima prova con canale non corretto e' stata rifiutata dalla validazione.
Dopo l'allineamento al canale osservato, la singola richiesta di lettura ha
restituito HTTP 200 ma azione Aura `ERROR`, con errore a monte:
`Unable to tunnel through proxy. Proxy returns "HTTP/1.1 503 Service Unavailable"`.
Non sono stati eseguiti retry continui o attivate funzionalita' dell'account.
Nessuna serie di consumi e' stata recuperata da questa operazione.

**HTTP 200 non e' sufficiente:** il futuro client dovra' verificare lo stato
della singola azione e l'eventuale errore applicativo nella risposta.
Un errore non deve essere trasformato in zero consumi o account senza forniture.

Non e' dimostrato che questa funzione Tendril corrisponda al monitoraggio
attuale dell'app. L'ipotesi di un percorso precedente o distinto resta da
verificare, non e' una conclusione sul funzionamento dell'app.
ENGIE descrive ufficialmente il [monitoraggio nell'app](https://www.engie.it/casa/per-te/app/)
e il [dettaglio dei consumi elettrici](https://www.engie.it/casa/magazine/monitoraggio-consumi-elettrici-casa/).

### Separazione delle operazioni

Il portale esegue anche richieste di contorno, incluse funzioni loyalty,
durante il proprio caricamento. Non riprodurre interi batch Aura intercettati.
Consentire soltanto singole operazioni di lettura verificate; il probe pubblico
non riproduce alcun batch o chiamata allo storico.

## Backend dell'app verificato, 16 settembre 2026

La successiva analisi dell'app Android `it.engie.appengie`, versione 10.1.0,
ha identificato un backend REST distinto dal portale Salesforce:
`https://api-mobileapp2022-prod.aws.engie.it/`.
I DTO e le chiamate di lettura sono stati confrontati con risposte di un account
autorizzato. Non sono state rimosse protezioni, installate app modificate o
replicate operazioni di scrittura. Nessun APK o payload dell'account nel progetto.

### Autenticazione

Il servizio usa Auth0 su `https://login.engie.it/`, con audience
`https://mobileapp.jwt`. Il primo accesso sperimentale ha usato Authorization
Code con PKCE S256, login manuale, state/nonce e validazione RS256 dell'ID token
tramite le chiavi dell'issuer. Una tolleranza di 30 secondi gestisce piccoli
scarti di orologio senza disabilitare la verifica temporale.

La configurazione pubblica dell'issuer e' disponibile nella
[discovery OIDC](https://login.engie.it/.well-known/openid-configuration).
L'access token va nell'header `sessionToken`, non `Authorization: Bearer`.
Sono presenti anche `x-api-key` e `locale: IT`: dalla b5 il parametro comune
proviene dal profilo applicativo incluso, separato dai token personali.
Non e' un'API pubblica documentata per terze parti.

Il rinnovo con `refresh_token` su `/oauth/token` e una successiva lettura sono
riusciti sia nel probe privato sia nel client asincrono del progetto.
La beta successiva ha verificato anche rinnovo con salvataggio e ricaricamento
in HA. Durata massima del consenso e challenge future restano da osservare;
la riautenticazione e' coperta da test offline, non da una revoca live forzata.

### Forniture mobile

`GET contracts/v2/user` restituisce `code: OK` e `listaContratti`.
Ogni contratto contiene `codContr` e `forniture`; ogni fornitura contiene
`id`, `commodity` (`Luce`/`Gas`), `attiva` (`y` osservato),
`dataAttivazione` (`YYYY-MM-DD`) e `punto.pod` oppure `punto.pdr`.
Identificativi, coordinate bancarie e anagrafica non vengono stampati dal probe.
Il parser seleziona solo i campi necessari e non presume la stabilita' degli ID
quando un contratto cambia.

### Consumi elettrici

Letture riuscite e implementate:

| Metodo/percorso GET | Parametri query |
| --- | --- |
| `consumptions/v2/power/getCommissioningDate` | `pod` |
| `consumptions/v3/power/daily` | `pod`, `lowerBoundDate`, `startYear`, `endYear` |
| `consumptions/v3/power/hourly` | `pod`, `lowerBoundDate`, `day` |

Date e limiti usano `YYYY-MM-DD`; gli anni sono stringhe a quattro cifre.
La data iniziale usa la commissioning date quando disponibile, altrimenti
l'attivazione, limitata al primo gennaio di due anni prima, come nel chiamante app.

Schema giornaliero osservato:

```text
code: "OK"
lastUpdate: "YYYY-MM-DD"
consumptionsList:
  startYear / endYear: "YYYY"
  years[]:
    timeReference: "YYYY"
    months[]:
      timeReference: "YYYY-MM"
      days[]:
        timeReference: "YYYY-MM-DD"
```

Ogni livello ha `totalValue` numerico, `totalType` e stringhe di presentazione.
Il parser legge solo il numero, senza interpretare `totalString` o `averageString`.
Le unita' elettriche nell'app sono kWh. `totalType` distingue `REAL`,
`ESTIMATED` e `NOT_PROVIDED`; valori futuri sconosciuti non diventano reali.

La risposta oraria ha `consumptionsList.day.day` (`YYYY-MM-DD`), totale del
giorno e `consumptions[]` con `timeReference: HH:00`, `totalValue`, `totalType`.
Il giorno ordinario verificato contiene 24 campioni. Il comportamento reale
nei giorni con ora ripetuta non e' ancora verificato: il parser rifiuta ore
ambigue o inesistenti senza indovinare l'offset. Test sintetici coprono questi casi.

I totali di anno/mese/giorno non coincidono necessariamente con la somma dei
campioni arrotondati. Vengono conservati separatamente, senza correzioni arbitrarie.
`lastUpdate` precede la data della richiesta: questi dati non sono in tempo reale.
La verifica live del client ha incluso rinnovo, forniture, commissioning date,
serie giornaliera e dettaglio orario, senza esportare token o dati dell'account.

### Fatture: schema statico e risposta live contraddittoria

L'app 10.1.0 dichiara `GET contracts/v2/invoices`, con query `contractId`
e `numberOfInvoices` opzionale. Il chiamante della cronologia passa `codContr`
come `contractId` e omette `numberOfInvoices`; le schede sintetiche dell'app
usano invece un limite. Il client b8 segue il percorso della cronologia,
una volta per codice contratto distinto, non per singola fornitura.

DTO verificati staticamente: `InvoicesResponse.response` contiene
`InvoicesHistoryResult`, con `invoices`, `inMaintenance` e `maintenanceMessage`.
Campi selezionati da `Invoice`:

| Campo API | Tipo / significato nell'app |
| --- | --- |
| `fiscalNumber` | Stringa, numero fiscale della fattura |
| `amount` | Numero, importo originale; presentazione in EUR nell'app |
| `unpaidRemainingAmount` | Numero, importo residuo da pagare |
| `emissionDate` | Stringa `YYYY-MM-DD`, data di emissione |
| `expiryDate` | Stringa `YYYY-MM-DD`, scadenza |
| `invoiceStatus` | `PAID`, `NOT_PAID`, `EXPIRED`, `PARTIALLY_PAID` |

La conversione dell'app conferma le date ISO e la presentazione numerica in
euro. Il parser conserva sconosciuti eventuali stati futuri. Non conserva
`pdfUrl`, dati di addebito, periodi o quantità fatturate non necessari ai sensori.

La lettura autorizzata del 16 settembre 2026 ha restituito **HTTP 200 e
`code: OK`**, ma anche **`engieErrorCode: 9`, `engieDetailedErrorCode: 9.91`**,
`response.invoices: []` e `inMaintenance: false`. Una verifica limitata con
`numberOfInvoices` esplicito ha prodotto lo stesso risultato. Non è una
risposta positiva con documenti, né una prova di assenza di fatture o debito.
Il significato esatto del codice non è confermato. `user/v4/dashboard`, letto
durante la ricerca, non ha fornito un riepilogo alternativo delle fatture e
non è stato aggiunto alle operazioni del client.

Parser e sensori b8 sono sperimentali, con fixture inventate per pagamenti
parziali, errori, scadenze, dati mancanti e duplicati. Una risposta con errore
applicativo non produce importi zero. Rimane aperta la verifica di fatture
reali e della copertura storica effettiva: [dettagli](INVOICES.md).

La b8 è stata installata e riavviata su HA 2026.9.2: tutte le 11 nuove entità
sono state create sul dispositivo Account. La lettura reale produce stato
fatture `error`, codici 9/9.91 e valori indisponibili; i sensori di consumo
precedenti restano disponibili. Verificati 113 test del client e 33 test HA
isolati, oltre al controllo della configurazione e alla corrispondenza dei file.

### Gas ancora non verificato con successo

Nell'app sono presenti queste letture, provate privatamente:

- `consumptions/v2/gas/getLastUpdateDate`, con `contractId`, `pdr`.
- `consumptions/v2/gas/monthly`, con `contractId`, `pdr`, `lowerBoundDate`,
  `supplyActivationDate`, `startYear`, `endYear`.

`contractId` deriva da `codContr` del contratto, non dall'ID Salesforce.
La data di aggiornamento ha restituito HTTP 404, `code: KO`, codici 9/9.53,
descrizione "Pdr non trovato". La lettura mensile ha restituito HTTP 422,
codici 9/9.54, descrizione "Input non valido". Questi errori **non dimostrano
che il consumo sia zero**, ne' spiegano da soli il motivo del grafico vuoto.
Non e' stata recuperata una risposta gas con misure: nessun parser o sensore gas
viene dichiarato funzionante. Le unita' Smc compaiono nell'app, ma resta da
verificare il payload di successo, compresi periodi e stime.

### Prezzi e condizioni economiche: verifica del 16 settembre 2026

La risposta `contracts/v2/user` espone per fornitura `productCode`,
`prodottoCodiceUnivoco`, `priceType`, `tipoContratto`, `inizioCE`, `fineCE`
e `durataCE`. Nella risposta osservata non contiene prezzi unitari numerici.
Le tipologie domestiche riconosciute e le regole di abbinamento sono descritte
in [TARIFFS.md](TARIFFS.md).

Il documento pubblico ENGIE
[223_pumd-00016](https://www.engie.it/documents/d/casa/223_pumd-00016)
riporta il codice completo `PUMD#00016`, componente energia, quote annue,
durata, perdite e PCS. La b10 include un catalogo di questa versione verificata;
non effettua download di documenti durante il polling e non deduce prezzi dal
nome commerciale. Fonte e impronta del PDF sono documentate; nessun contratto
personale è incluso nel repository.

Ulteriori letture dell'app, verificate staticamente e provate in sola lettura:

- `POST contracts/v2/documents/documentsList`, lista documenti con `contractId`,
  `fiscalCodeOrVat`, `practicesNames`: `contractKit` e `renewals` vuoti nella
  prova. Il verbo POST viene usato dall'app per una consultazione.
- `GET contracts/v2/invoicesCosts`, `contractId`, `dateFrom` opzionale:
  HTTP 200 e `OK`, ma codici ENGIE 9/9.91 e lista `costs` vuota. Il DTO contiene
  importi e periodi mensili, non quantità o prezzi unitari.
- `GET contracts/v2/getIndexGraphByCommodity`, `commodity=power` oppure `gas`:
  risposta riuscita con dodici valori `indexValue`/`periodLabel` e grafici
  PUN Index GME in €/kWh e PSVDA in €/Smc. Sono indici di mercato; non sono
  il prezzo personale di un'offerta a prezzo fisso. Per quelle indicizzate
  servono anche formula, spread, perdite e periodo contrattuale verificati.

Queste tre letture sono ricerca e non sono state aggiunte al client installato.

## Verifiche ancora necessarie

### Primo collegamento senza configurazione preesistente

La chiave `x-api-key` e' una risorsa statica comune del client mobile,
non una credenziale generata dal login del singolo account. La b5 la include
nel profilo applicativo: non chiede APK e non esegue un recupero da mirror.
Questo non costituisce un'approvazione del provider o una verifica delle
condizioni di distribuzione.

Verifiche senza sessioni personali, 16 settembre 2026:

- `GET authentication/v2/configurations` senza chiave restituisce HTTP 403.
- Lo stesso endpoint con il profilo comune restituisce HTTP 200: configurazione
  dell'app, flag manutenzione, versioni e opzioni, non dati di un account.
- Il codice del client aggiunge `x-api-key` dalle risorse; `sessionToken`
  viene invece dalla gestione delle credenziali OAuth. Sono due ruoli distinti.
- I grant `password` e `http://auth0.com/oauth/grant-type/password-realm`
  restituiscono HTTP 403, `unauthorized_client`. Le prove non hanno inviato
  username, password o OTP, ne' effettuato tentativi su account.
- La discovery OIDC e gli asset pubblici del login esaminati non forniscono
  un bootstrap senza chiave. La ricerca degli asset non e' esaustiva.
- Il dominio `engieapp.engie.it` non era risolvibile durante la prova.

La versione Android esaminata e' 10.1.0, pacchetto `it.engie.appengie`.
La firma v3 e' stata verificata con Android `apksigner`; il certificato SHA-256
`e2d2a82a217c536d7f5cd9ff809415da8dd581438b54d9265804e40d924a601d`
corrisponde alla dichiarazione ENGIE in
[assetlinks.json](https://login.engie.it/.well-known/assetlinks.json).
La verifica e' ricerca statica: il componente HA non esegue o interpreta APK.

Il prototipo b4 di importazione APK e' stato rimosso. La b5 risolve il
provisioning dei parametri, non il callback OAuth: il ritorno manuale descritto
in [SETUP.md](SETUP.md) rimane necessario.

### Criteri di completamento

1. Completare la verifica reale del primo login b5 e valutare un client dedicato.
2. Osservare la sessione nel tempo e verificare revoca/challenge reali in HA.
3. Consumi gas riusciti, rettifiche e dettaglio elettrico durante il cambio d'ora.
4. Verificare limiti e condizioni d'uso prima della distribuzione.
5. Ampliare solo con fixture inventate e test offline, mai risposte dell'account.

Nessun aggiramento di autenticazione, challenge o controlli di accesso.
Non assumere che un login riuscito una volta sia una soluzione mantenibile.
Verificare le condizioni d'uso applicabili prima della distribuzione.

Non pubblicare HAR, cookie, token, codici di autorizzazione o URL di redirect
completi. Anche query string, form Salesforce e storage del browser possono
contenere credenziali di sessione o dati identificativi.

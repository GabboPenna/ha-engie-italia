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
implementati download documenti, importi/scadenze o interpretazioni dei campi
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
Sono presenti anche `x-api-key` e `locale: IT`: la chiave dell'app non viene
distribuita in questo repository. Non e' un'API pubblica documentata per terze parti.

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

## Verifiche ancora necessarie

1. Rendere login e configurazione API distribuibili senza pubblicare chiavi dell'app.
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

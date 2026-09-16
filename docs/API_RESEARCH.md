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

## Verifiche ancora necessarie

1. Identificare il servizio del grafico attuale dell'app senza aggirare protezioni.
2. Verificare login ripetibile, scadenza/rinnovo e gestione delle challenge.
3. Verificare schema, unita', periodi, ritardo e dati mancanti di luce/gas.
4. Verificare limiti e condizioni d'uso prima della distribuzione.
5. Ampliare solo con fixture inventate e test offline, mai risposte dell'account.

Nessun aggiramento di autenticazione, challenge o controlli di accesso.
Non assumere che un login riuscito una volta sia una soluzione mantenibile.
Verificare le condizioni d'uso applicabili prima della distribuzione.

Non pubblicare HAR, cookie, token, codici di autorizzazione o URL di redirect
completi. Anche query string, form Salesforce e storage del browser possono
contenere credenziali di sessione o dati identificativi.

# ENGIE Italia

Progetto per una integrazione Home Assistant **non ufficiale, in sola lettura**
per le forniture luce e gas di ENGIE Italia.

**Stato: sviluppo preliminare. Non e' ancora installabile in Home Assistant
o tramite HACS. Client asincrono, forniture e consumi elettrici giornalieri/orari
verificati su un account autorizzato, incluso il rinnovo della sessione.
Primo accesso ancora interattivo; configurazione HA e consumi gas non pronti.**

Non affiliato, sponsorizzato o approvato da ENGIE. Il nome ENGIE appartiene
al rispettivo titolare.

## Obiettivo

Consultare da Home Assistant le forniture, i consumi, le letture e i dati
essenziali delle bollette disponibili nell'account, senza modificare nulla.

- Rilevamento delle forniture luce e gas associate all'account.
- Consumi con periodo di riferimento e distinzione fra effettivi e stimati,
  quando la sorgente fornisce questa informazione.
- Ultime letture, importi, scadenze e stato delle bollette, se esposti.
- Data di aggiornamento e diagnostica priva di credenziali e dati identificativi.
- Gestione esplicita di dati mancanti, sessione scaduta e servizio indisponibile.

**Un grafico gas vuoto non equivale a consumo zero.** Nessuna conversione
automatica fra metri cubi e Smc senza i dati necessari. Non sono promessi
tempo reale, dettaglio orario o disponibilita' identica fra luce e gas.

Sono esclusi pagamenti, invio di autoletture, modifiche contrattuali e qualsiasi
altra operazione di scrittura sull'account.

## Disponibile ora

- Modello dati indipendente da Home Assistant per forniture e intervalli di consumo.
- Validazione di valori, unita' e intervalli temporali, incluso il cambio d'ora.
- Riepilogo diagnostico con soli metadati selezionati.
- Parser delle forniture del portale, verificato durante una sessione autorizzata.
- Client asincrono per il servizio dell'app, limitato alle letture verificate.
- Parser forniture dell'app e consumi elettrici giornalieri/orari in kWh,
  con qualita', data di aggiornamento e totali ENGIE separati dai campioni.
- Rinnovo token in memoria, timeout, rispetto di `Retry-After` e nessun
  inoltro delle credenziali attraverso redirect HTTP.
- Test offline con dati interamente sintetici e CI su GitHub.
- Uno strumento opzionale che controlla il percorso pubblico di accesso,
  senza inserire credenziali o salvare una sessione.
- Una prova interattiva opzionale che legge le forniture dopo il login manuale
  e restituisce solo tipo e stato, senza esportare dati personali o sessioni.

Il client usa il backend mobile, distinto dallo storico del portale che nella
prima prova restituiva un errore 503 a monte. La lettura elettrica ora funziona;
non sono ancora implementate bollette o letture gas utilizzabili. Le risposte
gas osservate sono errori espliciti, non una serie vuota da interpretare come zero.

Le credenziali di sessione e la configurazione di accesso all'API devono essere
fornite al client tramite un canale privato. **Il repository non include chiavi
dell'app, token, un primo login mobile pubblico o persistenza delle credenziali.**
Il rinnovo verificato non significa ancora autenticazione HA pronta all'uso.
Dettagli in [client e limiti](docs/CLIENT.md) e [ricerca API](docs/API_RESEARCH.md).

## Sviluppo

Python 3.12 o successivo. Il client usa `aiohttp`; su Windows viene installato
anche il database dei fusi orari. Installare le dipendenze prima dei test:

```sh
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
```

Verifica opzionale del login pubblico, separata dai test e mai eseguita in CI:

```sh
python -m pip install -e ".[browser]"
python -m playwright install chromium
python tools/inspect_portal.py
```

Lo strumento apre un browser nuovo senza profilo personale, prosegue fino alla
pagina di login e termina. Non dimostra che autenticazione, rinnovo o lettura
dei consumi funzionino. Non produce HAR, screenshot, cookie o token su disco.

Prova opzionale con il proprio account, dopo la stessa installazione browser:

```sh
python tools/probe_account.py
```

Completare il login nella finestra aperta, incluso l'eventuale OTP. Non fornire
password nel terminale o nei file del progetto. La prova attende al massimo
10 minuti (modificabili con `--timeout`, in secondi), legge solo il riepilogo
delle forniture e chiude il browser. Chiudere la finestra annulla la prova.
Nessun HAR, screenshot, cookie o token viene esportato dallo strumento.
Non effettua chiamate allo storico, pagamenti, autoletture o modifiche contrattuali.
Il sito puo' eseguire proprie richieste di contorno durante il login e il
caricamento della dashboard; queste non vengono replicate dal progetto.

## Prossimi passi

1. Rendere il primo login e il rinnovo utilizzabili in HA, con persistenza sicura
   e configurazione API distribuibile; verificare condizioni e limiti d'uso.
2. Chiarire gli errori gas e verificare una risposta con consumi prima del parser.
3. Aggiungere l'integrazione nativa HA e test di configurazione/recupero.
4. Provare una beta privata; solo dopo preparare la distribuzione HACS.

Dettagli: [architettura](docs/ARCHITECTURE.md),
[ricerca API](docs/API_RESEARCH.md), [roadmap](docs/ROADMAP.md).

## Contributi e sicurezza

Leggere [CONTRIBUTING.md](CONTRIBUTING.md) e [SECURITY.md](SECURITY.md).
Non allegare mai bollette, HAR completi, credenziali, cookie, token,
codici cliente, POD/PDR o dati personali a issue e pull request.

Licenza [MIT](LICENSE).

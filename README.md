# ENGIE Italia

Progetto per una integrazione Home Assistant **non ufficiale, in sola lettura**
per le forniture luce e gas di ENGIE Italia.

**Stato: sviluppo preliminare. Non e' ancora installabile in Home Assistant
o tramite HACS e non recupera ancora i dati di un account ENGIE.**

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
- Test offline con dati interamente sintetici e CI su GitHub.
- Uno strumento opzionale che controlla il percorso pubblico di accesso,
  senza inserire credenziali o salvare una sessione.

Questi modelli **non sono parser delle risposte ENGIE**. Gli endpoint autenticati,
il formato dei dati e il rinnovo della sessione devono ancora essere verificati.

## Sviluppo

Python 3.12 o successivo. Il nucleo usa solo la libreria standard:

```sh
python -m unittest discover -s tests -v
```

Per lint, formato e tutti i test anche su Windows, installare le dipendenze
di sviluppo, incluso il database dei fusi orari:

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

## Prossimi passi

1. Verificare accesso autorizzato, rinnovo della sessione e prima lettura reale.
2. Implementare un client asincrono limitato alle chiamate di lettura verificate.
3. Aggiungere l'integrazione nativa HA e test di configurazione/recupero.
4. Provare una beta privata; solo dopo preparare la distribuzione HACS.

Dettagli: [architettura](docs/ARCHITECTURE.md),
[ricerca API](docs/API_RESEARCH.md), [roadmap](docs/ROADMAP.md).

## Contributi e sicurezza

Leggere [CONTRIBUTING.md](CONTRIBUTING.md) e [SECURITY.md](SECURITY.md).
Non allegare mai bollette, HAR completi, credenziali, cookie, token,
codici cliente, POD/PDR o dati personali a issue e pull request.

Licenza [MIT](LICENSE).

# ENGIE Italia

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/engie_italia/brand/dark_logo.png">
  <img alt="ENGIE" src="custom_components/engie_italia/brand/logo.png" width="220">
</picture>

Integrazione Home Assistant **non ufficiale, in sola lettura** per le forniture
ENGIE Italia. Non affiliata, sponsorizzata o approvata da ENGIE.

**Beta 0.1.0b3, accesso iniziale assistito.** Il client legge forniture luce/gas
e consumi elettrici; OAuth/PKCE gestisce login, rinnovo e persistenza della
sessione. La chiave API necessaria non viene distribuita nel repository:
questa beta non e' ancora un'installazione pubblica pronta all'uso.

## Funzioni

- Un dispositivo per fornitura, rilevato automaticamente.
- Stato della fornitura e disponibilita' dei dati.
- Luce: consumi dell'ultimo giorno, mese e anno disponibili con periodo,
  qualita', data dell'ultimo dato ENGIE e ultima sincronizzazione.
- Aggiornamento condiviso ogni 6 ore, configurabile fra 1 e 24 ore, e pulsante
  di aggiornamento manuale.
- Login nel sito ENGIE, eventuale OTP gestito da ENGIE, rinnovo automatico
  e riautenticazione quando il provider richiede un nuovo accesso.
- Diagnostica senza identificativi, credenziali o quantita' consumate.
- Configurazione guidata, connessione API riutilizzabile e loghi chiari/scuri.

**Gas: viene rilevata la fornitura, ma non sono ancora disponibili sensori
di consumo.** Le risposte osservate sono errori del servizio, non consumi zero.
Un account nuovo potrebbe non avere misure: la causa non e' confermata.
Bollette, importi e autoletture non sono implementati.
Prezzi unitari e tariffe automatiche restano in ricerca: nessun prezzo viene
dedotto dal nome dell'offerta e non e' richiesto un inserimento manuale.

I dati ENGIE arrivano in ritardo, non sono misure in tempo reale. I totali
sono quelli del provider, non somme dei campioni arrotondati. Nessuna
importazione nella dashboard Energy o creazione di falsi contatori cumulativi.
I misuratori locali e le altre integrazioni energetiche restano intatti.

## Installazione assistita

Richiede Home Assistant **2026.9.0 o successivo**, test del framework su 2026.9.2.

1. Copiare `custom_components/engie_italia` nella cartella `custom_components`
   della configurazione di HA e riavviare.
2. In **Impostazioni > Dispositivi e servizi > Aggiungi integrazione**, cercare
   **ENGIE Italia**.
3. Il popup **Prima di iniziare** elenca i requisiti. Scegliere **Ho la chiave:
   inizia** per inserire la configurazione tecnica della prova assistita, oppure
   **Non ho la chiave** per sapere come procedere e consultare lo stato del supporto.
   Non sostituire la chiave con password ENGIE o token Home Assistant. Lasciare
   invariati i parametri OAuth, salvo istruzioni specifiche.
4. Aprire il collegamento, completare login ed eventuale OTP. Copiare l'indirizzo
   completo di ritorno nel campo dedicato di HA. Il callback dell'app puo'
   mostrare una pagina vuota o un errore: interessa l'indirizzo
   `https://login.engie.it/android/it.engie.appengie/callback?...`.
5. Completare entro 10 minuti. Non condividere quell'indirizzo: contiene un
   codice temporaneo. Un tentativo scaduto richiede un nuovo accesso.

La [guida al primo collegamento](docs/SETUP.md) descrive anche il caso senza
chiave, l'uso da smartphone e il recupero degli errori. Le istruzioni essenziali
sono nel popup, non richiedono di leggere il repository.
Solo quando esistono account configurati appare anche **Usa una connessione
esistente**: riutilizza una configurazione API non ambigua, mai il consenso di
un altro account. Non e' un prerequisito per il primo collegamento.

La sessione viene salvata e riutilizzata dopo un riavvio; il browser puo' essere
chiuso. Revoca o scadenza definitiva del consenso richiedono un nuovo login:
non viene promessa una sessione perpetua.

### Perche' non torna automaticamente a HA?

Il client nativo verificato accetta il callback dell'app ENGIE, non quello di
Home Assistant. Il provider rifiuta il callback HA con `Callback URL mismatch`
e non abilita il grant `device_code`. Anche una sessione valida non permette
di leggere le forniture senza chiave API (HTTP 403).

Per un login completamente automatico occorre una configurazione applicativa
autorizzata dal provider: non basta cambiare la schermata o l'URL di ritorno.
La beta non usa proxy delle credenziali e non aggira questa protezione.

La struttura e `hacs.json` sono predisposti per un repository personalizzato,
ma il progetto **non e' nel catalogo HACS**. Distribuzione della configurazione
API e condizioni d'uso vanno chiarite prima di una beta pubblica autonoma.

## Sicurezza

Nessun pagamento, autolettura o modifica contrattuale/del profilo. Password
e OTP vengono inseriti solo nel sito ENGIE. Chiave API e token sono salvati
nel deposito privato HA con scritture atomiche e permessi restrittivi,
**non cifrati**. Proteggere host e backup; non pubblicare i file `.storage`.
Rimuovere l'integrazione elimina il deposito locale, non revoca automaticamente
il consenso presso ENGIE. Dettagli in [SECURITY.md](SECURITY.md).

## Sviluppo

Client indipendente: Python 3.12+. Il codice risiede in
`custom_components/engie_italia/api`, installato come package `engie_italia`.

```sh
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
```

Test HA in un ambiente separato Python 3.14:

```sh
python -m pip install homeassistant==2026.9.2
python -m unittest discover -s tests_ha -v
```

I test usano dati inventati e una configurazione temporanea, senza account reali.
I tool opzionali `inspect_portal.py` e `probe_account.py` sono strumenti di ricerca
del portale web, non configurano la sessione mobile. Richiedono l'extra
`browser` e Chromium.

Documentazione: [architettura](docs/ARCHITECTURE.md), [client](docs/CLIENT.md),
[ricerca API](docs/API_RESEARCH.md), [roadmap](docs/ROADMAP.md).
Contributi: [CONTRIBUTING.md](CONTRIBUTING.md). Codice: licenza [MIT](LICENSE).
Marchi e immagini: [attribuzione e limiti](docs/BRANDING.md).

<img src="https://raw.githubusercontent.com/GabboPenna/ha-engie-italia/main/custom_components/engie_italia/brand/logo@2x.png" alt="ENGIE" width="240">

# ENGIE Italia per Home Assistant

Forniture, consumi luce e gas, dati contrattuali e fatture ENGIE Italia in
Home Assistant.

[![Stato: beta 0.1.0b17](https://img.shields.io/badge/beta-0.1.0b17-f59e0b?style=flat-square)](https://github.com/GabboPenna/ha-engie-italia/releases/tag/v0.1.0b17)
[![Home Assistant 2026.9.0 o successivo](https://img.shields.io/badge/Home_Assistant-2026.9%2B-18bcf2?style=flat-square&logo=homeassistant&logoColor=white)](#requisiti)
[![Accesso in sola lettura](https://img.shields.io/badge/accesso-sola_lettura-10b981?style=flat-square)](https://github.com/GabboPenna/ha-engie-italia/blob/main/SECURITY.md)
[![Licenza del codice: MIT](https://img.shields.io/badge/licenza-MIT-64748b?style=flat-square)](https://github.com/GabboPenna/ha-engie-italia/blob/main/LICENSE)

[Installazione](#installazione) · [Collegare l'account](#collegare-laccount) ·
[Funzioni](#funzioni) · [Limiti](#limiti-importanti) ·
[Assistenza](https://github.com/GabboPenna/ha-engie-italia/issues)

Integrazione **non ufficiale, cloud e in sola lettura** per clienti domestici
ENGIE Italia. Non è affiliata, sponsorizzata o approvata da ENGIE.

La configurazione richiede soltanto l'accesso al proprio account sul sito
ufficiale ENGIE. Password ed eventuale OTP vengono inseriti nel sito ENGIE,
non in Home Assistant. Al termine si copia l'indirizzo finale del browser nel
popup dell'integrazione; la sessione viene poi conservata e rinnovata
automaticamente.

## Funzioni

| Area | Dati disponibili |
| :--- | :--- |
| **Forniture** | Rilevamento automatico di luce e gas, stato della fornitura e disponibilità dei dati. |
| **Consumi luce** | Ultimo giorno, mese e anno disponibili; data, periodo e qualità della misura; storico giornaliero importato nelle statistiche a lungo termine. |
| **Consumi gas** | Ultimo mese e anno disponibili in Smc, con periodo, qualità e data dell'ultimo dato pubblicato. |
| **Contratto** | Potenza impegnata e disponibile, scadenza delle condizioni economiche e finestra di autolettura gas, quando presenti. |
| **Servizi account** | Prossima bolletta prevista, addebito diretto e bolletta digitale. |
| **Fatture** | Ultimo documento, importi, scadenze e riepilogo delle fatture aperte. Funzione sperimentale, dipendente dai dati restituiti da ENGIE. |
| **Prezzi** | Componente energia e quota fissa annua per le versioni di offerta presenti nel catalogo verificato. Non è un calcolo completo della bolletta. |
| **Aggiornamenti** | Sincronizzazione condivisa ogni 6 ore, intervallo configurabile da 1 a 24 ore e pulsante di aggiornamento manuale. |
| **Diagnostica** | Informazioni tecniche anonimizzate, senza credenziali, identificativi della fornitura, consumi o importi. |

Ogni fornitura viene rappresentata da un dispositivo Home Assistant; i dati
condivisi, come fatture e servizi, sono raccolti nel dispositivo **Account**.

## Installazione

### HACS

Il progetto è ancora in attesa di inclusione nel catalogo HACS. Per installarlo
ora, aggiungilo come repository personalizzato:

1. Apri **HACS → Integrazioni**.
2. Dal menu in alto a destra scegli **Repository personalizzati**.
3. Inserisci `https://github.com/GabboPenna/ha-engie-italia` e seleziona la
   categoria **Integrazione**.
4. Apri **ENGIE Italia**, abilita le versioni beta e installa l'ultima release.
5. Riavvia Home Assistant.

La [guida HACS](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/HACS.md)
spiega anche aggiornamenti, passaggio da un'installazione manuale e problemi
di visualizzazione del logo.

### Installazione manuale

Scarica l'ultima release e copia la cartella
`custom_components/engie_italia` nella directory di configurazione di Home
Assistant:

```text
config/
└── custom_components/
    └── engie_italia/
        ├── manifest.json
        ├── __init__.py
        └── ...
```

Riavvia Home Assistant dopo la copia o dopo ogni aggiornamento manuale.

## Collegare l'account

1. Apri **Impostazioni → Dispositivi e servizi → Aggiungi integrazione** e
   cerca **ENGIE Italia**.
2. Seleziona **Accedi al tuo account ENGIE** e completa login ed eventuale OTP
   nel sito ufficiale, lasciando aperto il popup di Home Assistant.
3. Al termine copia **l'intero indirizzo dalla barra del browser**, anche se la
   pagina finale è vuota o mostra un errore.
4. Incolla l'indirizzo nel popup e premi **Invia** entro 10 minuti.

> [!IMPORTANT]
> L'indirizzo finale contiene un codice temporaneo: non condividerlo e non
> allegarlo alle segnalazioni. Non va incollato l'OTP né il testo della pagina.

![Configurazione da computer: accesso sul sito ENGIE e campo per l'indirizzo finale del browser](https://raw.githubusercontent.com/GabboPenna/ha-engie-italia/main/docs/images/setup-desktop.png)

<img src="https://raw.githubusercontent.com/GabboPenna/ha-engie-italia/main/docs/images/setup-mobile.png" alt="Configurazione di ENGIE Italia su smartphone" width="260">

Se il telefono apre direttamente l'app ENGIE, esegui il primo collegamento da
un browser su computer. La [guida al collegamento](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/SETUP.md)
contiene la procedura dettagliata, la riautenticazione e gli errori comuni.

Una volta collegato l'account, il browser può essere chiuso. La sessione viene
riutilizzata dopo riavvii e aggiornamenti; una revoca o una scadenza definitiva
può richiedere un nuovo accesso.

## Limiti importanti

- I dati provengono dai servizi cloud ENGIE e non sono misure in tempo reale.
- I consumi gas sono riepiloghi mensili e possono comparire con ritardo.
- Lo storico elettrico dipende dai giorni effettivamente pubblicati da ENGIE.
- Le fatture sono sperimentali: alcuni account ricevono dal servizio una
  risposta vuota o non disponibile anche quando altri dati funzionano.
- I prezzi coprono solo offerte e versioni presenti nel
  [catalogo verificato](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/TARIFFS.md);
  non includono tasse, trasporto, oneri o altri elementi della bolletta.
- Non sono implementati pagamenti, invio di autoletture, modifiche contrattuali
  o download dei PDF.

Un dato assente o una risposta non valida non vengono trasformati in consumo o
importo zero. Le forniture vengono aggiornate separatamente: un problema sul gas
non rende automaticamente indisponibili i consumi elettrici, e viceversa.

## Sicurezza e privacy

L'integrazione comunica direttamente con ENGIE e non usa server intermediari
del manutentore. I token della sessione vengono salvati nella cartella privata
`.storage` di Home Assistant con permessi restrittivi, ma **non sono cifrati**:
proteggi l'host e i backup e non pubblicare file di diagnostica non verificati,
backup, URL finali del browser o contenuti di `.storage`.

La rimozione dell'integrazione elimina il deposito locale, ma non revoca
automaticamente il consenso presso ENGIE. Consulta [Sicurezza e dati personali](https://github.com/GabboPenna/ha-engie-italia/blob/main/SECURITY.md)
prima di allegare materiale a una issue.

## Requisiti

- Home Assistant **2026.9.0 o successivo**.
- Un account ENGIE Italia con almeno una fornitura visibile nell'area clienti.
- Accesso a Internet da Home Assistant e dal browser usato per il collegamento.

La beta è verificata con il framework Home Assistant 2026.9.2 ed è utilizzata
su Home Assistant 2026.10. Le API ENGIE non sono pubbliche né garantite: un
cambiamento lato provider può richiedere un aggiornamento dell'integrazione.

## Documentazione

| Argomento | Documento |
| :--- | :--- |
| Primo collegamento, riautenticazione ed errori | [Guida al collegamento](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/SETUP.md) |
| Installazione e aggiornamenti con HACS | [Guida HACS](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/HACS.md) |
| Fatture, scadenze e automazioni | [Fatture](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/INVOICES.md) |
| Prezzi supportati e limiti del calcolo | [Tariffe](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/TARIFFS.md) |
| Funzioni previste | [Roadmap](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/ROADMAP.md) |
| Architettura e client Python | [Architettura](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/ARCHITECTURE.md) · [Client](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/CLIENT.md) |
| Segnalare un problema o contribuire | [Issue](https://github.com/GabboPenna/ha-engie-italia/issues) · [Contributi](https://github.com/GabboPenna/ha-engie-italia/blob/main/CONTRIBUTING.md) |

## Sviluppo

Il client indipendente richiede Python 3.12 o successivo. I test usano dati
interamente sintetici e non contattano account reali.

```sh
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
```

I test Home Assistant vengono eseguiti separatamente come indicato nel workflow
del repository. Prima di contribuire consulta [CONTRIBUTING.md](https://github.com/GabboPenna/ha-engie-italia/blob/main/CONTRIBUTING.md).

---

Codice distribuito con licenza **[MIT](https://github.com/GabboPenna/ha-engie-italia/blob/main/LICENSE)**.
I nomi e le immagini ENGIE appartengono ai rispettivi titolari; consulta
[attribuzione e limiti](https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/BRANDING.md).

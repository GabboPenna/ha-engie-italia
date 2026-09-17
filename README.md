<div align="center">

  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="custom_components/engie_italia/brand/dark_logo@2x.png">
    <img alt="ENGIE" src="custom_components/engie_italia/brand/logo@2x.png" width="240">
  </picture>

  <h1>ENGIE Italia per Home Assistant</h1>

  <p>Forniture, consumi elettrici, prezzi verificati e fatture, dentro Home Assistant.</p>

  <p>
    <a href="https://github.com/GabboPenna/ha-engie-italia/releases/tag/v0.1.0b12"><img alt="Stato: beta 0.1.0b12" src="https://img.shields.io/badge/beta-0.1.0b12-f59e0b?style=flat-square"></a>
    <a href="#installazione"><img alt="Home Assistant 2026.9.0 o successivo" src="https://img.shields.io/badge/Home_Assistant-2026.9%2B-18bcf2?style=flat-square&amp;logo=homeassistant&amp;logoColor=white"></a>
    <a href="SECURITY.md"><img alt="Accesso in sola lettura" src="https://img.shields.io/badge/accesso-sola_lettura-10b981?style=flat-square"></a>
    <a href="LICENSE"><img alt="Licenza del codice: MIT" src="https://img.shields.io/badge/licenza-MIT-64748b?style=flat-square"></a>
  </p>

  <p>
    <a href="#installazione">Installazione</a> ·
    <a href="docs/SETUP.md">Guida al collegamento</a> ·
    <a href="docs/ROADMAP.md">Roadmap</a> ·
    <a href="https://github.com/GabboPenna/ha-engie-italia/issues">Segnala un problema</a>
  </p>

</div>

Integrazione **non ufficiale e in sola lettura** per le forniture ENGIE Italia.
Non affiliata, sponsorizzata o approvata da ENGIE.

**Non servono APK o chiavi API da inserire.** La connessione all'app è già
predisposta: accedi sul sito ufficiale ENGIE e incolli in HA l'indirizzo finale
del browser. Il ritorno manuale resta necessario; la sessione viene poi salvata
e rinnovata automaticamente. [Procedura e limiti →](docs/SETUP.md)

## Uno sguardo alla configurazione

Schermate reali della beta **0.1.0b7** su Home Assistant **2026.9.2**.
Le immagini mostrano solo la finestra di collegamento, senza dati dell'account.

<table>
  <tr>
    <th width="70%">Da computer</th>
    <th width="30%">Da smartphone</th>
  </tr>
  <tr>
    <td valign="top">
      <a href="docs/images/setup-desktop.png">
        <picture>
          <source media="(prefers-color-scheme: dark)" srcset="docs/images/setup-desktop-dark.png">
          <img src="docs/images/setup-desktop.png" alt="Configurazione da computer: accesso sul sito ENGIE e campo per l'indirizzo finale del browser" width="580">
        </picture>
      </a>
    </td>
    <td valign="top">
      <img src="docs/images/setup-mobile.png" alt="La stessa configurazione di ENGIE Italia sullo schermo di uno smartphone" width="240">
    </td>
  </tr>
</table>

Il campo resta vuoto finché non completi l'accesso sul sito ENGIE. Se il telefono
apre direttamente l'app ENGIE, esegui il primo collegamento da un computer.

## Cosa trovi in Home Assistant

| Funzione | Disponibile nella beta |
| :--- | :--- |
| **Forniture** | Rilevamento automatico, un dispositivo per fornitura, stato e disponibilità dei dati. |
| **Consumi luce** | Ultimo giorno, mese e anno disponibili, con periodo, qualità e data dell'ultimo dato ENGIE. |
| **Fatture · sperimentale** | Ultima fattura, importo, fatture aperte, residuo da pagare e scadenze sul dispositivo Account. [Sensori e limiti](docs/INVOICES.md). |
| **Prezzi · sperimentale** | Componente energia in €/kWh e €/Smc e quota fissa annua, per le versioni di offerta verificate. [Copertura e limiti](docs/TARIFFS.md). |
| **Aggiornamenti** | Sincronizzazione condivisa ogni 6 ore, intervallo da 1 a 24 ore, pulsante manuale e data dell'ultima sincronizzazione. |
| **Accesso** | Login e OTP sul sito ENGIE, rinnovo della sessione e riautenticazione quando richiesta. |
| **Diagnostica** | Informazioni tecniche senza identificativi, credenziali, quantità consumate o importi. |
| **Interfaccia** | Configurazione guidata senza parametri tecnici e logo per tema chiaro e scuro. |

> [!IMPORTANT]
> **La beta rileva le forniture gas, ma non espone ancora i loro consumi.**
> Download PDF, pagamenti e autoletture non sono implementati. I dati ENGIE sono
> differiti: non rappresentano misure in tempo reale.

Le risposte gas osservate sono errori del servizio, non consumi zero. Un account
nuovo potrebbe non avere misure: la causa non è confermata. La b10 abbina il
codice completo dell'offerta alle condizioni economiche pubbliche verificate.
La b11 include **16 versioni di Energia PuntoFisso Mono 12 mesi**:
[elenco e prezzi](docs/TARIFFS.md#catalogo-verificato-nella-b11). Rinnovi e prezzi
indicizzati restano in ricerca. Nessun prezzo viene dedotto dal nome dell'offerta
o richiesto manualmente. I valori escludono tasse e altri oneri della bolletta.

Dalla b12 le offerte sono raccolte in un [catalogo JSON dedicato](custom_components/engie_italia/api/data/tariffs.json),
per aggiungere versioni verificate senza modificare la logica di abbinamento.
[Come aggiornare il catalogo](docs/TARIFFS.md#catalogo-json-e-aggiornamenti).

I totali di consumo sono quelli del provider, non somme dei campioni arrotondati.
Non è prevista l'importazione nella dashboard Energy o la creazione di falsi
contatori cumulativi. I misuratori locali e le altre integrazioni energetiche
restano intatti.

### Fatture e automazioni

La b8 aggiunge **11 sensori sul dispositivo Account**: riferimento, importo,
data e scadenza dell'ultima fattura; numero di fatture disponibili, aperte e
scadute; totale residuo da pagare, prima scadenza aperta, stato e sincronizzazione.
Il residuo tiene conto dei pagamenti parziali e ogni documento viene contato
una sola volta, anche con luce e gas sullo stesso contratto.

Il cambiamento di **Ultima fattura** può essere usato nelle proprie automazioni,
insieme a **Fatture disponibili**. L'integrazione espone i sensori; notifiche e
automazioni restano una scelta dell'utente. [Significato e uso dei sensori](docs/INVOICES.md).

> [!NOTE]
> **La lettura di una fattura reale resta da confermare.** Schema e chiamata sono
> verificati nell'app; l'account di prova restituisce una lista vuota con codice
> ENGIE `9.91`, nonostante `OK`. In questo caso gli importi risultano indisponibili:
> la risposta non viene interpretata come conferma di zero da pagare.

## Installazione

Richiede Home Assistant **2026.9.0 o successivo**; test del framework su **2026.9.2**.

1. **Installa il componente.** Copia la cartella `custom_components/engie_italia`
   nella configurazione di Home Assistant, quindi riavvia HA:

   ```text
   config/
   └── custom_components/
       └── engie_italia/
           ├── manifest.json
           ├── __init__.py
           └── …
   ```

2. **Aggiungi l'integrazione.** Apri **Impostazioni → Dispositivi e servizi →
   Aggiungi integrazione** e cerca **ENGIE Italia**.
3. **Accedi a ENGIE.** Nella finestra **Collega il tuo account ENGIE**, apri il
   collegamento al sito ufficiale e completa login ed eventuale OTP. Lascia aperta
   la finestra di configurazione HA.
4. **Completa il collegamento.** Incolla l'indirizzo finale del browser nel campo
   di HA e premi **Invia** entro 10 minuti.

> [!TIP]
> La pagina finale può essere vuota o mostrare un errore: serve **l'indirizzo
> completo della barra del browser**, con `code` e `state`, non il codice OTP.
> Non condividere quell'indirizzo.

La [guida al primo collegamento](docs/SETUP.md) descrive il ritorno manuale,
l'uso da smartphone e gli errori. Non servono Android, file dell'app o altri
account configurati. Ogni account richiede il proprio consenso ENGIE.

La sessione viene salvata e riutilizzata dopo un riavvio; il browser può essere
chiuso. Revoca o scadenza definitiva del consenso richiedono un nuovo login:
non viene promessa una sessione perpetua.

<details>
<summary><strong>Perché il browser non torna automaticamente a Home Assistant?</strong></summary>


Il client nativo verificato accetta il callback dell'app ENGIE, non quello di
Home Assistant. Il provider rifiuta il callback HA con `Callback URL mismatch`
e non abilita i grant `device_code`, `password` o `password-realm`.
Anche una sessione valida non permette
di leggere le forniture senza chiave API (HTTP 403).

Per un login completamente automatico occorre una configurazione applicativa
autorizzata dal provider: non basta cambiare la schermata o l'URL di ritorno.
La beta non usa proxy delle credenziali e non aggira questa protezione.

</details>

### HACS

La beta si distribuisce tramite repository personalizzato, con controlli
automatici HACS e hassfest. Il progetto **non è ancora nel catalogo HACS**:
la comparsa nella ricerca generale richiede l'approvazione della
[richiesta d'inclusione #11034](https://github.com/hacs/default/pull/11034).
[Procedura per provarla e stato del catalogo](docs/HACS.md).
Non vengono distribuiti APK.
I parametri comuni inclusi non costituiscono un'approvazione ENGIE e possono
cambiare. Le condizioni d'uso/distribuzione restano da verificare
prima di proporla all'uso generalizzato.

## Sicurezza

Nessun pagamento, autolettura o modifica contrattuale/del profilo. Password
e OTP vengono inseriti **solo nel sito ENGIE**. Nessun server intermediario,
download, caricamento o parser di APK. Chiave API e token sono salvati
nel deposito privato HA con scritture atomiche e permessi restrittivi,
**non cifrati**. Proteggere host e backup; non pubblicare i file `.storage`.
Rimuovere l'integrazione elimina il deposito locale, non revoca automaticamente
il consenso presso ENGIE. Dettagli in [SECURITY.md](SECURITY.md).

## Sviluppo

Client indipendente: **Python 3.12+**. Il codice risiede in
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

## Documentazione e contributi

| Cerchi… | Parti da qui |
| :--- | :--- |
| Primo accesso o soluzione di un errore | [Guida al collegamento](docs/SETUP.md) |
| Fatture, scadenze e sensori per automazioni | [Guida alle fatture](docs/INVOICES.md) |
| Repository personalizzato e controlli HACS | [Guida HACS](docs/HACS.md) |
| Funzioni previste e stato dei lavori | [Roadmap](docs/ROADMAP.md) |
| Struttura dell'integrazione | [Architettura](docs/ARCHITECTURE.md) |
| Utilizzo del client Python | [Documentazione client](docs/CLIENT.md) |
| Dettagli delle API ENGIE | [Ricerca API](docs/API_RESEARCH.md) |
| Segnalare un problema o contribuire | [Issue](https://github.com/GabboPenna/ha-engie-italia/issues) · [Contributi](CONTRIBUTING.md) |

---

Codice distribuito con licenza **[MIT](LICENSE)**. Marchi e immagini appartengono
ai rispettivi titolari: [attribuzione e limiti](docs/BRANDING.md).

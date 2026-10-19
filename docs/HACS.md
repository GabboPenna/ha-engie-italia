# Installazione con HACS

ENGIE Italia è una beta pubblica inclusa nel catalogo predefinito HACS. La
[richiesta di inclusione #11034](https://github.com/hacs/default/pull/11034) è
stata approvata e unita il 19 ottobre 2026. Non è necessario aggiungere un
repository personalizzato.

Stato verificato il **19 ottobre 2026**.

## Requisiti

- HACS già installato e configurato;
- Home Assistant 2026.9.0 o successivo;
- accesso amministrativo a Home Assistant;
- disponibilità ad usare una release contrassegnata come beta.

## Prima installazione

1. Apri **HACS → Integrazioni**.
2. Cerca e apri **ENGIE Italia** nel catalogo.
3. Abilita la visualizzazione delle versioni beta, se richiesto, scegli
   l'ultima release e avvia il download.
4. Riavvia Home Assistant.
5. Apri **Impostazioni → Dispositivi e servizi → Aggiungi integrazione** e cerca
   **ENGIE Italia**.

La release pubblica corrente è
[v0.1.0b21](https://github.com/GabboPenna/ha-engie-italia/releases/tag/v0.1.0b21).
Se HACS propone una beta precedente, seleziona esplicitamente la versione dal
menu di download.

## Aggiornamenti

Quando HACS segnala una nuova versione:

1. leggi le note della release;
2. avvia l'aggiornamento da HACS;
3. riavvia Home Assistant se richiesto;
4. controlla che l'integrazione sia caricata e che i sensori tornino disponibili.

Account, sessione ed entità sono conservati fuori dalla cartella del componente.
Un normale aggiornamento non richiede la rimozione e la nuova aggiunta
dell'integrazione.

## Passare da installazione manuale a HACS

La cartella deve chiamarsi già `custom_components/engie_italia`.

1. Cerca **ENGIE Italia** nel catalogo predefinito HACS.
2. Installa con HACS la stessa versione o una versione successiva.
3. Riavvia Home Assistant.

Non rimuovere prima la voce dell'account: la configurazione e la sessione
esistenti possono essere riutilizzate. È comunque prudente avere un backup
recente di Home Assistant.

## Problemi comuni

### L'integrazione non compare in “Aggiungi integrazione”

Verifica che il download HACS sia terminato, che esista la cartella
`custom_components/engie_italia` e che Home Assistant sia stato riavviato.
Ricarica completamente il browser dopo il riavvio.

### HACS mostra una versione precedente

Apri il menu del repository e scegli **Aggiorna informazioni**. Se la versione
resta precedente, scegli **Scarica di nuovo** e seleziona esplicitamente
l'ultima beta.

### Logo assente nella ricerca HACS

Alcune versioni di HACS possono mostrare `icon not available` nella ricerca,
anche se le immagini locali incluse nell'integrazione vengono caricate
correttamente da Home Assistant dopo il download. Non indica
un'installazione incompleta.

Il logo e le icone sono contenuti in `custom_components/engie_italia/brand/` e
sono serviti direttamente da Home Assistant nelle pagine dell'integrazione.

### La scheda HACS mostra una documentazione vecchia

HACS aggiorna periodicamente i metadati del repository. Dal menu di ENGIE Italia
scegli **Aggiorna informazioni** per forzare il controllo; per aggiornare i file
installati usa invece **Scarica di nuovo** e riavvia Home Assistant.

## Controlli del progetto

Ogni push e pull request eseguono:

- test offline del client su Python 3.12 e 3.14;
- test dell'integrazione in un ambiente Home Assistant isolato;
- validazione del catalogo tariffe e del pacchetto distribuibile;
- Ruff, hassfest e validazione HACS senza esclusioni.

I test usano dati sintetici e non ricevono credenziali o dati di account reali.
Il superamento dei validatori controlla struttura e compatibilità del progetto,
ma non garantisce la disponibilità futura dei servizi cloud ENGIE.

Riferimenti: [uso del catalogo HACS](https://www.hacs.xyz/docs/use/repositories/dashboard/),
[integrazioni HACS](https://www.hacs.xyz/docs/use/repositories/type/integration/)
e [requisiti per la pubblicazione](https://www.hacs.xyz/docs/publish/integration/).

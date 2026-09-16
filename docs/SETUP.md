# Primo collegamento

Questa guida parte da una installazione senza alcun account ENGIE configurato.
L'integrazione e' non ufficiale, in sola lettura e ancora in beta assistita.

## Cosa serve

- Un account ENGIE Italia con forniture visibili e accesso all'eventuale OTP.
- Una chiave API ottenuta per la prova assistita.
- Un browser per aprire il sito ENGIE e copiare l'indirizzo finale.

La chiave API identifica la connessione tecnica al servizio: **non e' la
password ENGIE, il codice OTP o un token Home Assistant**. HA non la genera.
Password e OTP si inseriscono esclusivamente sul sito ENGIE.

## Non ho la chiave

Nel popup scegliere **Non ho la chiave**. Se si partecipa a una prova assistita,
chiedere la configurazione tecnica a chi segue la prova. Altrimenti consultare
lo [stato dell'accesso e l'assistenza](https://github.com/GabboPenna/ha-engie-italia/issues/1).

Non abbiamo ancora una procedura pubblica verificata per ottenere e distribuire
la configurazione API. Non promettiamo che una richiesta di assistenza dia accesso
alla beta. Senza la chiave non si puo' completare il collegamento: non provare
password o token alternativi. Non condividere dati riservati nelle issue.

## Procedura

1. In **Impostazioni > Dispositivi e servizi > Aggiungi integrazione**, selezionare
   **ENGIE Italia**. Nel popup leggere i requisiti e scegliere **Ho la chiave: inizia**.
2. Incollare la sola chiave API e premere **Invia**. Lasciare chiusa la sezione
   OAuth: il Client ID predefinito non richiede modifiche nella prova ordinaria.
3. Aprire il collegamento ENGIE mostrato dal popup. Completare login ed eventuale
   OTP sul sito ENGIE, mantenendo aperta anche la configurazione HA.
4. Copiare tutto l'indirizzo finale dalla barra del browser. Il ritorno previsto
   e' `https://login.engie.it/android/it.engie.appengie/callback` con i parametri
   `code` e `state`. Una pagina finale vuota o con errore non esclude un indirizzo
   utilizzabile; non copiare invece il testo della pagina, l'OTP o l'URL iniziale.
5. Tornare a HA, incollare l'indirizzo completo e premere **Invia** entro 10 minuti
   dall'apertura del passaggio di accesso. L'indirizzo contiene un codice temporaneo:
   non inviarlo al manutentore o in una issue.

HA verifica il ritorno e salva la sessione privatamente. I successivi rinnovi
sono automatici finche' ENGIE li consente; dopo una revoca puo' servire un nuovo login.

## Problemi durante il login

- **Il telefono apre l'app invece del browser:** ricominciare la configurazione
  da HA in un browser su computer, senza riutilizzare il vecchio link.
- **Indirizzo non valido o tentativo scaduto:** aprire nuovamente il link del popup,
  completare un nuovo accesso e copiare il nuovo indirizzo. Non riprovare quello vecchio.
- **ENGIE non risponde:** riprovare piu' tardi con un nuovo accesso, senza cambiare
  credenziali per tentativi.
- **Salvataggio della sessione non riuscito:** riprovare il salvataggio dal popup;
  non e' necessario rifare subito il login. Verificare spazio e permessi su HA.

Il client ENGIE attuale non accetta un ritorno OAuth diretto a Home Assistant.
Il passaggio manuale e la chiave iniziale sono limiti della beta, non opzioni
che l'utente deve cercare o abilitare nel proprio account.

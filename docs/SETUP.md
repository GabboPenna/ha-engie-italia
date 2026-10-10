# Collegare un account ENGIE

Questa guida descrive il primo collegamento, la riautenticazione e gli errori
più comuni. L'integrazione è non ufficiale e accede ai dati in sola lettura.

## Prima di iniziare

Servono:

- un account ENGIE Italia funzionante;
- almeno una fornitura visibile nell'area clienti;
- un browser dal quale sia possibile copiare l'indirizzo completo della pagina;
- Home Assistant 2026.9.0 o successivo con ENGIE Italia già installata.

Password ed eventuale OTP vengono inseriti esclusivamente nel sito ufficiale
ENGIE. Home Assistant non li richiede e non li salva.

## Primo collegamento

1. Apri **Impostazioni → Dispositivi e servizi → Aggiungi integrazione** e
   seleziona **ENGIE Italia**.
2. Nel popup **Collega il tuo account ENGIE**, apri **Accedi al tuo account
   ENGIE**. Lascia aperto il popup di Home Assistant.
3. Completa login ed eventuale OTP nel sito ENGIE.
4. Al termine copia **tutto l'indirizzo dalla barra del browser**. La pagina può
   essere vuota o mostrare un errore: è l'indirizzo che serve, non il contenuto.
5. Torna al popup di Home Assistant, incolla l'indirizzo nel campo
   **Indirizzo finale del browser** e premi **Invia** entro 10 minuti.

L'indirizzo corretto inizia normalmente così:

```text
https://login.engie.it/android/it.engie.appengie/callback?code=...&state=...
```

Deve contenere entrambi i parametri `code` e `state`. Non incollare l'OTP, il
link iniziale di accesso o il testo visualizzato nella pagina.

> [!WARNING]
> L'indirizzo finale contiene un codice temporaneo associato al tentativo di
> accesso. Non condividerlo, non inserirlo nelle issue e non salvarlo in note o
> screenshot pubblici.

## Dopo il collegamento

Home Assistant crea un dispositivo **Account** e un dispositivo per ogni
fornitura rilevata. Il primo aggiornamento può richiedere qualche istante.

La sessione viene salvata nella cartella privata `.storage` e rinnovata quando
possibile. Il browser può essere chiuso; riavvii e normali aggiornamenti
dell'integrazione non richiedono un nuovo accesso.

Ogni account ENGIE va autorizzato separatamente. Aggiungere un secondo account
non modifica quello già configurato.

## Perché bisogna copiare l'indirizzo finale?

Il sito ENGIE conclude l'accesso su un indirizzo destinato al proprio client e
non può tornare direttamente al popup di Home Assistant. Incollando
l'indirizzo finale, l'integrazione completa in modo controllato lo stesso
tentativo avviato dal popup.

Il passaggio è manuale, ma password e OTP restano nel sito ENGIE e non vengono
inoltrati a Home Assistant o a server del manutentore.

## Uso da smartphone

Il collegamento può funzionare da browser mobile se al termine rimane visibile
la barra degli indirizzi. Se il telefono apre automaticamente l'app ENGIE o non
permette di copiare l'indirizzo finale, usa un browser su computer per il primo
accesso. Dopo il collegamento non è necessario continuare a usare quel computer.

## Riautenticazione

Se ENGIE revoca o non rinnova più la sessione, Home Assistant mostra la richiesta
di riconfigurazione:

1. apri la notifica di riparazione o il menu dell'integrazione;
2. accedi con **lo stesso account ENGIE** già associato;
3. copia e incolla il nuovo indirizzo finale seguendo la procedura precedente.

La riautenticazione non può sostituire l'account configurato con un altro. Per
usare un'identità diversa, rimuovi la voce esistente e aggiungi un nuovo account.

## Problemi comuni

### Il telefono apre l'app ENGIE

Ripeti il collegamento da un browser su computer. Non serve modificare
l'installazione di Home Assistant.

### Indirizzo non valido

Copia nuovamente l'intero contenuto della barra degli indirizzi. Verifica che
comprenda `code` e `state` e non aggiungere virgolette o altro testo.

### L'indirizzo appartiene a un altro accesso

Ogni popup crea un tentativo distinto. Usa il link mostrato nel popup ancora
aperto e incolla lì il relativo indirizzo finale. Non mescolare schede o
tentativi precedenti.

### Tentativo scaduto o già usato

Riapri il collegamento proposto dal popup e completa un nuovo accesso. Il codice
finale è temporaneo e può essere inviato una sola volta.

### ENGIE non risponde

Attendi qualche minuto e riprova. Se il problema continua, verifica che il sito
e l'app ENGIE siano raggiungibili prima di aprire una issue.

### Il salvataggio non riesce

Controlla spazio libero e permessi della configurazione di Home Assistant. Se il
popup invita a premere di nuovo **Invia**, usa lo stesso indirizzo senza ripetere
subito il login.

### L'accesso riesce ma alcuni dati mancano

Forniture, consumi, fatture e metadati provengono da servizi distinti. Un account
nuovo può non avere ancora misure gas o storico sufficiente; il servizio fatture
può inoltre risultare non disponibile mentre i consumi funzionano. Controlla i
sensori **Dati di consumo** e **Dati fatture** prima di considerarlo un errore di
autenticazione.

## Chiedere assistenza

Apri una [issue](https://github.com/GabboPenna/ha-engie-italia/issues) indicando:

- versione dell'integrazione e di Home Assistant;
- tipo di fornitura interessata;
- testo esatto dell'errore, senza dati personali;
- diagnostica scaricata da Home Assistant, dopo averne controllato il contenuto.

Non allegare indirizzi finali del browser, token, cookie, file `.storage`, HAR,
fatture, POD/PDR, codici cliente o schermate con dati personali.

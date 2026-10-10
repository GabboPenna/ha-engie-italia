# Sicurezza e dati personali

ENGIE Italia per Home Assistant è un'integrazione non ufficiale, cloud e in sola
lettura. Non è affiliata, sponsorizzata o approvata da ENGIE.

## Operazioni consentite

Il componente legge forniture, consumi, informazioni contrattuali e, quando il
servizio le rende disponibili, fatture e scadenze. Non implementa pagamenti,
autoletture, download di documenti o modifiche dell'account e del contratto.

## Accesso all'account

Password ed eventuale OTP vengono inseriti esclusivamente nel sito ufficiale
ENGIE. Il componente non li riceve, non li salva e non usa server intermediari
del manutentore.

Il popup di configurazione crea un tentativo temporaneo protetto da PKCE,
`state` e `nonce`. L'indirizzo finale copiato dal browser contiene un codice
monouso: non va condiviso, registrato nei log o allegato alle issue.

I parametri applicativi inclusi nell'integrazione sono comuni al client e non
identificano un utente. Da soli non consentono di leggere forniture o consumi:
serve sempre una sessione autorizzata dal titolare dell'account. La loro
presenza non costituisce approvazione del progetto da parte di ENGIE né
garanzia che il servizio rimanga invariato.

## Deposito locale

Per ogni account, Home Assistant salva configurazione e token in un file
`.storage/engie_italia.auth.<hash>`. Le scritture sono atomiche e il file usa
permessi `0600`, ma il contenuto **non è cifrato**.

Amministratori, accesso al disco e backup possono quindi esporre la sessione.
Proteggi host e copie di sicurezza e non pubblicare file `.storage`. La config
entry contiene soltanto un identificativo derivato, non i token dell'account.

Il rinnovo salva il token ruotato prima di proseguire con le letture. Se il
disco non è scrivibile, la nuova sessione può restare soltanto in memoria e un
riavvio può richiedere un nuovo accesso.

Rimuovere l'integrazione elimina il deposito locale corrente, ma non revoca
automaticamente il consenso presso ENGIE e non cancella le copie presenti nei
backup. La revoca va gestita anche dal proprio account ENGIE, quando disponibile.

## Dati in Home Assistant

I sensori possono esporre consumi, date, importi, scadenze e riferimenti delle
fatture. Recorder può conservarli nello storico secondo la configurazione
locale di Home Assistant. Il componente non crea un archivio separato e non
scarica i PDF delle bollette.

La diagnostica usa un elenco esplicito di metadati ammessi ed esclude token,
identificativi della fornitura, codici offerta, consumi, importi e riferimenti
delle fatture. Controlla comunque ogni file prima di condividerlo.

## Log e segnalazioni

Non attivare trace HTTP completi su un sistema reale: URL, query e risposte
possono contenere POD/PDR, codici cliente o altri dati personali. Un HAR del
browser non è una diagnostica sicura.

Per problemi ordinari indica versione, tipo di fornitura e messaggio di errore
anonimizzato. Non allegare credenziali, cookie, token, indirizzi finali del
browser, file `.storage`, backup, bollette, nomi, indirizzi, email, codici
cliente, POD/PDR o codici fiscali.

Per una vulnerabilità usa la
[segnalazione privata GitHub](https://github.com/GabboPenna/ha-engie-italia/security/advisories/new),
se disponibile. Non aprire una issue pubblica con dettagli sfruttabili o dati
personali.

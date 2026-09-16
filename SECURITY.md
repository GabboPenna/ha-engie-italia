# Sicurezza e dati personali

Il progetto e' una beta non ufficiale, non ancora destinata all'uso generalizzato.
Non pubblicare credenziali personali, cookie, token, HAR completi, storage del
browser, bollette, nomi, indirizzi, email, codici cliente, POD/PDR o codici fiscali.
I file ignorati da Git non sono una protezione dei dati: controllare sempre
diff, allegati e contenuto dei commit.

## Parametri applicativi e autorizzazione

`api/app.py` contiene il parametro `x-api-key` comune distribuito nel client
Android ENGIE Italia esaminato. Il client ID OAuth e' anch'esso applicativo,
non un client secret. Questi valori non identificano un utente e **non concedono
accesso alle forniture**: le letture richiedono il token di un account autorizzato.

Non confondere la presenza tecnica di questi parametri con un'approvazione
del progetto da parte di ENGIE o una garanzia sulla loro stabilita'. Le condizioni
d'uso e di distribuzione restano da verificare prima dell'uso generalizzato.
Nuovi parametri non verificati o chiavi di servizi terzi non vanno aggiunti
come se fossero configurazione pubblica.

Il componente non richiede, scarica, interpreta o esegue APK. Non usa mirror,
server del manutentore o copie di configurazioni preesistenti per preparare
un nuovo account. Il client HTTP accetta i parametri in memoria; in HA vengono
forniti dal profilo applicativo incluso o dal deposito del proprio account
durante la riautenticazione.

Password e OTP si inseriscono esclusivamente sul sito ENGIE. Rispettare
challenge, CAPTCHA e limiti del servizio; nessun aggiramento dei controlli.
Il ritorno OAuth manuale e' temporaneo: PKCE, state, nonce e firma RS256
proteggono il completamento. Non condividere codici o URL completi di callback.

## Deposito locale

In HA, `.storage/engie_italia.auth.<hash>` conserva configurazione e token con
permessi `0600` e scritture atomiche. Il deposito **non e' cifrato**:
amministratori, disco e backup possono esporlo. Proteggere host e backup.
La config entry contiene solo un identificativo derivato, non chiavi o token.

Ogni account richiede una nuova autorizzazione. La riautenticazione non puo'
sostituire l'identita' dell'account configurato. Rimuovere l'integrazione elimina
il deposito locale, non revoca il consenso presso ENGIE e non elimina vecchi backup.

Il rinnovo salva il token ruotato prima di proseguire con le letture. Se il disco
non e' scrivibile, il token nuovo resta in RAM per ritentare il salvataggio.
Un crash tra rinnovo remoto e scrittura puo' richiedere un nuovo login:
non esiste una transazione atomica fra HA e il provider.

## Log e segnalazioni

I sensori fatture espongono numero fiscale, date e importi in Home Assistant:
Recorder può conservarli nello storico secondo la configurazione locale.
Il componente non scarica PDF e non conserva un archivio separato di bollette.
La diagnostica esclude riferimenti, date, importi e conteggi delle fatture;
i modelli omettono questi dati da `repr`.

Gli errori espongono messaggi fissi e codici selezionati. Non attivare trace
HTTP che registrino richieste autenticate: POD/PDR possono essere nelle query.
I modelli contengono identificativi privati: `repr` li omette, ma
`dataclasses.asdict` e serializzazioni indiscriminate non sono diagnostica sicura.
Il riepilogo diagnostico usa una lista di metadati ammessi; non rende sicuro un HAR.

Per segnalazioni sensibili usare la segnalazione privata GitHub, se abilitata:
https://github.com/GabboPenna/ha-engie-italia/security/advisories/new

Per problemi ordinari indicare versione, tipo di fornitura ed errore anonimizzato,
senza allegati personali.

# Sicurezza e dati personali

Il progetto e' una beta assistita, non ancora destinata all'uso generalizzato.

Non pubblicare credenziali, cookie, token, HAR completi, storage del browser,
bollette, nomi, indirizzi, email, codici cliente, POD/PDR o codici fiscali.
I file ignorati da Git sono una precauzione, non una protezione dei dati:
controllare sempre diff, allegati e contenuto dei commit.

Le prove autenticate devono usare un account autorizzato, conservando
i dati necessari solo localmente e con accesso limitato. Rispettare OTP,
CAPTCHA e limiti del servizio. Non aggirare controlli di accesso.

Il client riceve chiave API e token tramite parametri privati. In HA, un deposito
`.storage/engie_italia.auth.<hash>` li conserva con permessi `0600` e scritture
atomiche. Il deposito non e' cifrato: amministratori, accesso al disco e backup
possono esporlo. Proteggere host e backup con cifratura appropriata.
La config entry contiene solo un identificativo derivato, non chiavi o token.
Rimuovere l'integrazione elimina il deposito locale, non revoca il consenso
dal provider; copie nei backup rimangono fino alla loro eliminazione.

Il rinnovo salva il token ruotato prima di proseguire con le letture. Se il disco
non e' scrivibile, il token nuovo rimane in RAM per ritentare il salvataggio.
Un crash tra rinnovo remoto e scrittura locale puo' richiedere un nuovo login:
non esiste una transazione atomica fra HA e il provider.

Non includere nel repository chiavi estratte dall'app, APK,
codici OAuth, URL completi di callback o risposte dell'account. Gli errori pubblici
espongono solo messaggi fissi e codici numerici selezionati. Non attivare trace
HTTP che registrino richieste autenticate: POD/PDR possono essere nelle query.
Anche i modelli normalizzati contengono identificativi privati: `repr` li omette,
ma `dataclasses.asdict` e serializzazioni indiscriminate non sono diagnostica sicura.

Il riepilogo diagnostico attuale accetta solo modelli normalizzati e produce
metadati selezionati. Non rende sicuro un payload arbitrario o un HAR.

Per segnalazioni sensibili usare la segnalazione privata GitHub, se abilitata:
https://github.com/GabboPenna/ha-engie-italia/security/advisories/new

Non aprire una issue pubblica contenente dati riservati. Per problemi ordinari
indicare versione, tipo di fornitura e errore anonimizzato, senza allegati personali.

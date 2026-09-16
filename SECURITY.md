# Sicurezza e dati personali

Il progetto e' preliminare e non e' ancora destinato all'uso in produzione.

Non pubblicare credenziali, cookie, token, HAR completi, storage del browser,
bollette, nomi, indirizzi, email, codici cliente, POD/PDR o codici fiscali.
I file ignorati da Git sono una precauzione, non una protezione dei dati:
controllare sempre diff, allegati e contenuto dei commit.

Le future prove autenticate devono usare un account autorizzato, conservando
i dati necessari solo localmente e con accesso limitato. Rispettare OTP,
CAPTCHA e limiti del servizio. Non aggirare controlli di accesso.

Il client mobile riceve chiave API e token tramite parametri privati e li mantiene
solo in memoria. Non includere nel repository chiavi estratte dall'app, APK,
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

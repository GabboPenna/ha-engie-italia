# Ricerca API

## Osservazioni pubbliche, 16 settembre 2026

Il sito ufficiale collega lo Spazio Clienti a
`https://4you.engie.it/spazioclienti/ACMAAuthentication`.
Da un browser nuovo sono state osservate richieste Salesforce Aura,
fra cui `/spazioclienti/aura`. Premendo Accedi si raggiunge
`https://login.engie.it/u/login/identifier`, con un campo email.

Non sono state inserite credenziali o interrogate forniture. Il percorso
pubblico non dimostra la disponibilita' di API consumi o di un rinnovo
sessione utilizzabile da un'integrazione. Lo strumento `inspect_portal.py`
verifica solo la navigazione al login.

Nella ricerca preliminare non e' stata trovata documentazione pubblica
delle API consumer italiane. Le integrazioni ENGIE per altri Paesi non
dimostrano compatibilita' con l'account italiano.

L'app italiana dichiara consultazione di consumi luce/gas, contratti,
bollette e autolettura gas. Le funzioni dell'app non garantiscono che
gli stessi dati siano accessibili dal portale web o con la stessa API.

Fonti:
- [Spazio Clienti ENGIE](https://www.engie.it/casa/per-te/spazio-clienti/)
- [App ufficiale](https://play.google.com/store/apps/details?id=it.engie.appengie)
- [Portale pubblico](https://4you.engie.it/spazioclienti/ACMAAuthentication)

## Verifica autenticata da svolgere

1. Accedere interattivamente al proprio account, rispettando OTP e CAPTCHA.
2. Osservare soltanto consultazione forniture e consumi; distinguere le
   operazioni di lettura dai pulsanti che modificano l'account.
3. Identificare endpoint, schema minimo e dati realmente disponibili,
   senza esportare pubblicamente richieste o risposte personali.
4. Verificare scadenza/rinnovo, limiti e differenze fra luce e gas.
5. Scrivere fixture sintetiche e test prima di implementare il client.

Nessun aggiramento di autenticazione, challenge o controlli di accesso.
Non assumere che un login riuscito una volta sia una soluzione mantenibile.
Verificare le condizioni d'uso applicabili prima della distribuzione.

Non pubblicare HAR, cookie, token, codici di autorizzazione o URL di redirect
completi. Anche query string, form Salesforce e storage del browser possono
contenere credenziali di sessione o dati identificativi.

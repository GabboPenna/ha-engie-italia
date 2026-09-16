# Roadmap

## Fase 0: fondamenta

- [x] Perimetro sola lettura e stato del progetto esplicito.
- [x] Modelli per luce/gas e valori mancanti con test sintetici.
- [x] Diagnostica selezionata, documentazione e CI.
- [x] Strumento di verifica del percorso pubblico di login.

## Fase 1: prova di fattibilita' autenticata

- [x] Accesso manuale autorizzato e prima lettura delle forniture del portale.
- [x] Parser forniture e probe interattivo con riepilogo privo di identificativi.
- [x] Identificazione e lettura del backend dell'app, distinto dal portale.
- [x] Login interattivo PKCE e rinnovo della sessione in memoria verificati.
- [x] Persistenza privata atomica dei token e riautenticazione dello stesso account.
- [x] Profilo applicativo comune incluso, senza APK o inserimento manuale di chiavi.
- [x] Nuovo consenso per ogni account, senza riutilizzare sessioni altrui.
- [x] Istruzioni nel popup e test del flusso con credenziali sintetiche.
- [x] Flusso da installazione vuota direttamente al login, test HA con account sintetico.
- [x] Nuovo login reale nella UI b6: account verificato caricato in HA.
- [x] Percorso con ritorno manuale accettato; istruzioni operative semplificate nella b7.
- [ ] Eventuale ritorno automatico con callback HA autorizzato dal provider (non bloccante).
- [x] Schema elettrico giornaliero/orario ordinario verificato: kWh, periodi e ritardo.
- [ ] Verifica live delle ore ripetute e delle rettifiche storiche.
- [x] Forniture senza serie di consumi distinte da consumi pari a zero nei modelli.
- [ ] Differenze e disponibilita' reali dei consumi gas verificate sul servizio.
- [ ] Limiti e condizioni d'uso verificati, campioni esclusivamente sintetici.

Se l'accesso richiede challenge incompatibili con un aggiornamento autonomo,
documentare il limite prima di procedere con un'integrazione installabile.

### Primo collegamento

La prova con l'account rimosso ha confermato il limite della b3. Il prototipo
b4 con upload APK e' stato abbandonato: la b5 include direttamente i parametri
comuni del client mobile e rimuove caricamento, parser e dipendenze Android.
Il bootstrap dell'app con tali parametri restituisce HTTP 200 senza una
sessione personale; le letture dell'account richiedono sempre il suo token.
Il percorso e' coperto con dati sintetici e il nuovo account risulta caricato
in HA dopo il login b6. Nessun ripristino da backup usato per questa verifica.

Il primo tentativo reale con la b5 e' fallito; il messaggio generico non
permetteva di ricostruire la causa. La b6 distingue validazione del ritorno,
scadenza, stato di altro tentativo, scambio codice, identita' e sessione.
Un incolla errato non cambia piu' il link e un errore prima dello scambio
non consuma il tentativo. Log solo con codici fissi, mai URL o token.
La causa esatta del primo tentativo fallito non e' ricostruibile, ma il nuovo
accesso e' riuscito. Il ritorno manuale e' accettato come soluzione: non e'
un blocco aperto da sostituire prima di proseguire. La b7 lascia nel popup
soltanto le azioni richieste all'utente, senza dettagli implementativi.

Il recupero automatico della configurazione API e il ritorno OAuth a HA sono
due problemi distinti: risolvere uno non dimostra di aver risolto l'altro.

## Fase 2: client e Home Assistant

- [x] Client asincrono per forniture e consumi elettrici, provato sull'account.
- [x] Test per scadenza/rinnovo, errori rete, 429, dati mancanti e duplicati.
- [ ] Schema gas di successo e relativo client/parser.
- [x] Polling condiviso prudente, refresh manuale e cache commissioning giornaliera.
- [x] b9: letture identiche contemporanee deduplicate per account; annullamenti
  isolati e cache commissioning invalidata al cambio contratto/attivazione.
- [x] Rettifiche dei riepiloghi correnti sostituiscono la lettura precedente,
  anche a parità di data e con importi/consumi in diminuzione; test sintetici.
- [ ] Importazione storica con gestione delle rettifiche.
- [x] Config flow/reauth e coordinatore condiviso per account.
- [x] Sensori, identificativi stabili, disponibilita' e diagnostica HA.
- [x] Endpoint fatture, parametri e DTO verificati staticamente nell'app.
- [x] b8: ultima fattura, importi residui, conteggi e scadenze per account;
  deduplicazione, pagamenti parziali e indisponibilità coperti da test sintetici.
- [ ] Confermare una risposta con fatture reali: prova attuale vuota con
  codici ENGIE 9/9.91 nonostante `OK`; nessuna conferma di zero da pagare.
- [ ] Eventuali ulteriori letture aggiunte solo dopo verifica dei dati disponibili.
- [ ] Recupero automatico dei prezzi unitari verificabili, senza stime dal nome offerta.
- [x] Beta privata su dati reali, senza alterare altre integrazioni energetiche.

## Fase 3: distribuzione

- [x] Manifest, traduzioni italiano/inglese e installazione assistita documentata.
- [x] Test isolati sul framework Home Assistant e beta installata.
- [x] Icone e loghi locali per tema chiaro/scuro e schermi ad alta densita'.
- [x] Workflow automatici hassfest e HACS per push, PR e controllo settimanale.
- [x] Validazione HACS e hassfest della b9 superata in CI, senza esclusioni.
- [x] Repository personalizzato HACS aggiunto e download b9 verificato su HA,
  con passaggio dalla copia manuale e account conservato dopo il riavvio.
- [ ] Eventuale richiesta di inclusione nel catalogo HACS, separata dal punto precedente.

L'importazione storica nella dashboard Energy e' successiva alla corretta
gestione dei dati: nessuna promessa di tempo reale o di calcolo completo bolletta.

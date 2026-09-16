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
- [ ] Configurazione API distribuibile senza provisioning privato.
- [x] Schema elettrico giornaliero/orario ordinario verificato: kWh, periodi e ritardo.
- [ ] Verifica live delle ore ripetute e delle rettifiche storiche.
- [x] Forniture senza serie di consumi distinte da consumi pari a zero nei modelli.
- [ ] Differenze e disponibilita' reali dei consumi gas verificate sul servizio.
- [ ] Limiti e condizioni d'uso verificati, campioni esclusivamente sintetici.

Se l'accesso richiede challenge incompatibili con un aggiornamento autonomo,
documentare il limite prima di procedere con un'integrazione installabile.

## Fase 2: client e Home Assistant

- [x] Client asincrono per forniture e consumi elettrici, provato sull'account.
- [x] Test per scadenza/rinnovo, errori rete, 429, dati mancanti e duplicati.
- [ ] Schema gas di successo e relativo client/parser.
- [x] Polling condiviso prudente, refresh manuale e cache commissioning giornaliera.
- [ ] Importazione storica con gestione delle rettifiche.
- [x] Config flow/reauth e coordinatore condiviso per account.
- [x] Sensori, identificativi stabili, disponibilita' e diagnostica HA.
- [ ] Bollette/letture aggiunte solo dopo verifica dei dati disponibili.
- [x] Beta privata su dati reali, senza alterare altre integrazioni energetiche.

## Fase 3: distribuzione

- [x] Manifest, traduzioni italiano/inglese e installazione assistita documentata.
- [x] Test isolati sul framework Home Assistant e beta installata.
- [ ] Asset di integrazione e validazione completa HACS.
- [ ] Repository personalizzato HACS.
- [ ] Eventuale richiesta di inclusione nel catalogo HACS, separata dal punto precedente.

L'importazione storica nella dashboard Energy e' successiva alla corretta
gestione dei dati: nessuna promessa di tempo reale o di calcolo completo bolletta.

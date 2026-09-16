# Roadmap

## Fase 0: fondamenta

- [x] Perimetro sola lettura e stato del progetto esplicito.
- [x] Modelli per luce/gas e valori mancanti con test sintetici.
- [x] Diagnostica selezionata, documentazione e CI.
- [x] Strumento di verifica del percorso pubblico di login.

## Fase 1: prova di fattibilita' autenticata

- [x] Accesso manuale autorizzato e prima lettura delle forniture del portale.
- [x] Parser forniture e probe interattivo con riepilogo privo di identificativi.
- [ ] Autenticazione autonoma e rinnovo della sessione verificati.
- [ ] Schema consumi elettrici verificato: unita', periodi, granularita', ritardo.
- [x] Forniture senza serie di consumi distinte da consumi pari a zero nei modelli.
- [ ] Differenze e disponibilita' reali dei consumi gas verificate sul servizio.
- [ ] Limiti e condizioni d'uso verificati, campioni esclusivamente sintetici.

Se l'accesso richiede challenge incompatibili con un aggiornamento autonomo,
documentare il limite prima di procedere con un'integrazione installabile.

## Fase 2: client e Home Assistant

- [ ] Client asincrono con sole operazioni di lettura autorizzate.
- [ ] Test per scadenza sessione, errori rete, 429, dati parziali e rettifiche.
- [ ] Config flow/reauth e coordinatore condiviso per account.
- [ ] Sensori, identificativi stabili, disponibilita' e diagnostica HA.
- [ ] Bollette/letture aggiunte solo dopo verifica dei dati disponibili.
- [ ] Beta privata su dati reali, senza alterare altre integrazioni energetiche.

## Fase 3: distribuzione

- [ ] Manifest, traduzioni, asset di integrazione e documentazione di installazione.
- [ ] Validazione Home Assistant e HACS; prima versione utilizzabile.
- [ ] Repository personalizzato HACS.
- [ ] Eventuale richiesta di inclusione nel catalogo HACS, separata dal punto precedente.

L'importazione storica nella dashboard Energy e' successiva alla corretta
gestione dei dati: nessuna promessa di tempo reale o di calcolo completo bolletta.

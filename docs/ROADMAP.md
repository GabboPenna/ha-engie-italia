# Roadmap

La roadmap descrive il lavoro ancora utile per rendere l'integrazione più
completa e affidabile. Lo storico dettagliato delle versioni è disponibile
nelle [release GitHub](https://github.com/GabboPenna/ha-engie-italia/releases).

Aggiornata al **19 ottobre 2026**.

## Stato attuale

- [x] Accesso guidato con login e OTP sul sito ENGIE.
- [x] Sessione persistente, rinnovo e riautenticazione dello stesso account.
- [x] Lettura separata delle forniture luce e gas.
- [x] Consumi elettrici giornalieri, mensili e annuali.
- [x] Importazione dello storico elettrico nelle statistiche a lungo termine.
- [x] Consumi gas mensili e annuali in Smc.
- [x] Stato, qualità e periodo dei dati senza valori zero inventati.
- [x] Riepilogo sperimentale di fatture, importi e scadenze.
- [x] Metadati contrattuali e servizi account selezionati.
- [x] Catalogo locale di prezzi verificati su condizioni pubbliche.
- [x] Catalogo indipendente per account solo luce, solo gas o duali.
- [x] Inventario ripetibile degli open data storici del Portale Offerte.
- [x] Configurazione, opzioni, diagnostica anonimizzata e immagini locali.
- [x] Distribuzione iniziale tramite repository HACS personalizzato.
- [x] Inclusione nel catalogo predefinito HACS tramite la
  [richiesta #11034](https://github.com/hacs/default/pull/11034).
- [x] Test client, test Home Assistant, hassfest e validazione HACS in CI.

## Priorità

### Affidabilità dei dati

- [ ] Confermare il comportamento delle fatture con account che restituiscono
  documenti reali. La risposta finora osservata può essere vuota con codice
  applicativo ENGIE anche quando consumi e contratto funzionano.
- [ ] Verificare rettifiche storiche, giorni con cambio d'ora e serie parziali
  su più tipologie di account.
- [ ] Ampliare le fixture sintetiche quando vengono osservate nuove strutture,
  senza includere payload o identificativi reali nel repository.
- [ ] Gestire nuovi campi soltanto dopo averne verificato significato,
  disponibilità e comportamento in caso di dati mancanti.

### Copertura delle offerte

- [x] Automatizzare l'inventario delle offerte ENGIE negli open data storici
  del Portale Offerte, mantenendo separate commodity e condizioni incompatibili.
- [ ] Riesaminare i codici con snapshot economici conflittuali senza scegliere
  arbitrariamente una delle versioni.
- [ ] Modellare esplicitamente sconti, offerte indicizzate e fasce prima di
  importarli nel catalogo.
- [ ] Studiare rinnovi e cambi prodotto senza riutilizzare il prezzo iniziale.
- [ ] Valutare offerte indicizzate e multiorarie con modelli espliciti, senza
  dedurre prezzi dal nome commerciale.
- [ ] Mantenere fonti, impronte dei documenti e regole di validità nel catalogo.

### Esperienza di configurazione

- [ ] Ridurre il passaggio manuale dell'indirizzo finale se ENGIE renderà
  disponibile un ritorno autorizzato compatibile con Home Assistant.
- [ ] Migliorare ulteriormente i messaggi di errore sulla base di casi reali
  anonimizzati.
- [ ] Verificare il flusso su più browser desktop e mobili.

### Distribuzione

- [x] Ottenere l'inclusione nel catalogo HACS; la
  [richiesta #11034](https://github.com/hacs/default/pull/11034) è stata
  approvata e unita il 19 ottobre 2026.
- [ ] Verificare ogni release su installazione pulita e aggiornamento dalla
  versione precedente.
- [ ] Continuare a testare le nuove versioni stabili di Home Assistant senza
  aumentare inutilmente la versione minima richiesta.

## Fuori perimetro

Il progetto resta intenzionalmente in sola lettura. Non sono pianificati:

- pagamenti o gestione dei metodi di pagamento;
- invio di autoletture;
- modifiche contrattuali, anagrafiche o delle preferenze dell'account;
- download o archiviazione dei PDF delle fatture;
- calcolo completo e fiscalmente affidabile della bolletta;
- sostituzione di contatori o misuratori locali in tempo reale.

Le proposte che richiedono operazioni di scrittura devono essere discusse prima
in una issue e non verranno incluse senza API, autorizzazioni e garanzie adeguate.

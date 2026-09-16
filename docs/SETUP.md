# Primo collegamento

La beta b7 usa direttamente i parametri comuni del client mobile ENGIE Italia.
**Non servono APK, chiavi API da inserire, Android o account gia' presenti in HA.**
L'integrazione rimane non ufficiale e in sola lettura.

## Procedura

1. In **Impostazioni > Dispositivi e servizi > Aggiungi integrazione**, scegli
   **ENGIE Italia**. Compare direttamente la schermata di accesso.
2. Apri **Accedi al tuo account ENGIE** e completa login ed eventuale OTP sul sito
   ufficiale, mantenendo aperta anche la configurazione HA.
3. Copia tutto l'indirizzo finale dalla barra del browser. Il ritorno previsto
   e' `https://login.engie.it/android/it.engie.appengie/callback` con i parametri
   `code` e `state`. La pagina puo' essere vuota o mostrare un errore: serve
   l'indirizzo, non il testo della pagina, l'OTP o il link iniziale.
4. Torna a HA, incolla l'indirizzo completo e premi **Invia** entro 10 minuti.
   Non condividere questo indirizzo: contiene un codice temporaneo.

HA verifica il codice con PKCE e l'identita' con firma, issuer, audience e nonce.
Salva privatamente la sessione e la rinnova; normalmente riavvii e aggiornamenti
non richiedono un nuovo login. Revoca o scadenza definitiva possono richiederlo.
Ogni nuovo account richiede una propria autorizzazione, anche se altri account
ENGIE sono gia' configurati. Un account rimosso non viene ripristinato da backup.

## Perche' copiare ancora un indirizzo?

Il client dell'app ENGIE accetta il suo callback, non quello di Home Assistant.
Il server rifiuta sia il callback HA sia i grant per device code e accesso diretto
con password. I parametri applicativi inclusi risolvono la preparazione della
connessione, **non eliminano questi vincoli OAuth**.

Non chiediamo password o OTP a HA e non usiamo proxy per intercettarli.
Un ritorno automatico standard richiede un client con callback HA autorizzato
dal provider. Questo passaggio manuale resta un limite della beta.

## Smartphone e problemi comuni

- **Il telefono apre l'app ENGIE:** completa il primo collegamento da un browser
  su computer, dove puoi copiare l'indirizzo finale.
- **Indirizzo incompleto:** ricopia l'intero indirizzo, senza testo aggiuntivo.
  Questo errore non cambia il tentativo: il collegamento attuale resta valido.
- **Tentativo diverso:** usa il link dello stesso popup HA in cui incolli il
  ritorno e tienilo aperto. Non mescolare schede o link di tentativi precedenti.
- **Tentativo scaduto o gia' utilizzato:** usa il nuovo link nel popup e completa
  un nuovo accesso. I codici gia' inviati a ENGIE non vengono ritentati.
- **Errore recupero chiavi:** il codice non e' ancora stato inviato. Puoi
  riprovare con lo stesso indirizzo, entro la durata del tentativo.
- **Codice rifiutato, identita' o sessione non valida:** il messaggio identifica
  il passaggio fallito. Segnalalo senza includere indirizzo, codice o token.
- **Pagina finale vuota o con errore:** controlla l'indirizzo, non il contenuto.
  Deve essere il callback indicato sopra con `code` e `state`.
- **Problemi di salvataggio:** controlla spazio e permessi di HA; ritenta il
  salvataggio dal popup senza ripetere subito il login.
- **Vecchia schermata con APK o chiavi:** aggiorna l'integrazione, riavvia HA,
  ricarica completamente il browser e riapri la configurazione.
- **ENGIE cambia o revoca i parametri del client:** puo' servire un aggiornamento
  dell'integrazione. Non si tratta necessariamente di una password errata.

## Dati e dipendenze

I parametri applicativi sono comuni al client, non credenziali personali:
da soli non consentono di leggere forniture o consumi. Il componente non
scarica, interpreta o installa APK e non contatta mirror o server del manutentore.
I token personali restano nel deposito privato HA, non cifrato: proteggi
host e backup e non allegare file `.storage` a issue pubbliche.

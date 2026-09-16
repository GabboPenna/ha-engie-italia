# Repository personalizzato HACS

Il progetto è una beta non ufficiale e non è incluso nel catalogo HACS.
La b9 ha superato entrambi i validatori ufficiali, HACS e hassfest, senza esclusioni.
I controlli automatici di struttura non confermano il funzionamento delle API
ENGIE, le condizioni di distribuzione o l'esito di un'installazione completa.
Il download del tag pubblico **v0.1.0b9** attraverso un repository personalizzato è stato verificato
con HACS 2.0.5 e Home Assistant 2026.9.2, partendo da una copia manuale della b8.
Dopo il riavvio l'account è rimasto caricato, con le stesse 22 entità e gli stessi
valori dei consumi. Le fatture hanno mantenuto l'indisponibilità dovuta a 9/9.91.
La prova non conferma i dati che il servizio non ha restituito.
HACS riconosce la versione installata e disponibile come `v0.1.0b9`, senza
aggiornamenti o riavvii pendenti dopo la verifica.

## Installare la beta

Occorrono HACS già configurato e Home Assistant 2026.9.0 o successivo.

1. Apri HACS, il menu in alto a destra e **Repository personalizzati**.
2. Inserisci `https://github.com/GabboPenna/ha-engie-italia`, scegli la categoria
   **Integrazione** e aggiungi il repository.
3. Apri **ENGIE Italia** e abilita la visualizzazione delle versioni beta del
   repository. Scegli **v0.1.0b9** nel selettore della versione e scaricala.
   Se è già installata, usa **Riscarica / Redownload**. Controlla le
   [note della beta](https://github.com/GabboPenna/ha-engie-italia/releases/tag/v0.1.0b9):
   consumi gas e lettura di fatture reali restano da confermare.
4. Riavvia Home Assistant e segui la [guida al collegamento](SETUP.md).

La release è contrassegnata come **pre-release** su GitHub. Non viene presentata
come versione stabile: a seconda della versione di HACS può essere necessario
abilitare le beta o selezionarla esplicitamente nella finestra di download.

Per passare da una copia manuale a HACS, la cartella del componente deve essere
la stessa: `custom_components/engie_italia`. Conserva la config entry dell'account;
la sessione risiede nel deposito privato HA, esterno alla cartella del componente.
Un aggiornamento non richiede intenzionalmente la cancellazione dell'account.

## Logo assente nella ricerca HACS

Con **HACS 2.0.5** la ricerca può mostrare **icon not available** per ENGIE Italia.
È un limite noto del pannello HACS: legge le icone dal vecchio archivio online
Home Assistant Brands, mentre questa integrazione include le immagini nella
cartella locale `custom_components/engie_italia/brand/`, secondo i requisiti attuali.

Verifica del **16 settembre 2026**, con la b9 su HA 2026.9.2: l'API locale di
Home Assistant restituisce icona e logo, chiari e scuri, con HTTP 200 e contenuto
identico ai file installati. L'URL usato da HACS restituisce invece il segnaposto
"icon not available". Il componente è installato correttamente; reinstallarlo
o essere accettati nel catalogo HACS non cambia l'origine delle immagini.

La correzione della ricerca è proposta in
[hacs/frontend #945](https://github.com/hacs/frontend/pull/945) insieme a
[hacs/integration #5388](https://github.com/hacs/integration/pull/5388): alla data
della verifica sono aperte e non incluse in una release HACS.
Il repository Home Assistant Brands
[non accetta nuovi marchi per integrazioni personalizzate](https://github.com/home-assistant/brands/blob/master/.github/workflows/close-new-custom-integrations.yml).
Il logo locale resta utilizzabile nell'interfaccia nativa di Home Assistant.

## Comparire nella ricerca di HACS

Un repository personalizzato compare solo nell'HACS di chi lo ha aggiunto.
Per renderlo trovabile agli altri utenti occorre l'inclusione in `hacs/default`:
controlli superati, una release pubblicata dopo i controlli e accettazione della
richiesta da parte dei manutentori. La candidatura non equivale all'inclusione.

La [richiesta hacs/default #11034](https://github.com/hacs/default/pull/11034)
è stata aperta il **16 settembre 2026** ed è in attesa di accettazione.
La [beta pubblica v0.1.0b9](https://github.com/GabboPenna/ha-engie-italia/releases/tag/v0.1.0b9)
è già disponibile tramite la procedura qui sopra.

La [procedura ufficiale](https://www.hacs.xyz/docs/publish/include/) segnala che
la revisione può richiedere mesi. Dopo l'accettazione il repository entra nel
successivo aggiornamento del catalogo. `hacs.json` dichiara il Paese `IT`.
La ricerca **Aggiungi integrazione** di Home Assistant trova il componente
dopo che HACS lo ha scaricato e HA è stato riavviato.

## Controlli automatici

Il workflow `Validate integration` esegue i validatori ufficiali **hassfest**
e **HACS**, senza esclusioni, su push e pull request. È disponibile anche
l'avvio manuale; sul ramo predefinito viene ripetuto settimanalmente.
Il workflow `Tests` esegue separatamente i test offline su Python 3.12/3.14
e quelli del framework Home Assistant in una configurazione temporanea.

Le azioni sono referenziate da commit specifici. I contenitori dei validatori
sono quelli pubblicati dalle rispettive azioni e possono aggiornarsi: un nuovo
fallimento va esaminato, non nascosto disabilitando controlli.

La validazione usa soltanto il token GitHub del job con permesso di lettura;
nessun account ENGIE, token HA, segreto applicativo personalizzato o payload reale
viene passato ai job. Tutti i file necessari al componente sono nella sua
cartella, incluse traduzioni e immagini locali del marchio.

Fonti: [requisiti delle integrazioni HACS](https://www.hacs.xyz/docs/publish/integration/),
[azione di validazione HACS](https://www.hacs.xyz/docs/publish/action/),
[repository personalizzati](https://www.hacs.xyz/docs/faq/custom_repositories/).

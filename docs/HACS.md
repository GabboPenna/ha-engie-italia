# Repository personalizzato HACS

Il progetto è una beta non ufficiale e non è incluso nel catalogo HACS.
I controlli automatici di struttura non confermano il funzionamento delle API
ENGIE, le condizioni di distribuzione o l'esito di un'installazione completa.
La prova di installazione e aggiornamento mediante HACS resta aperta nella
[issue #3](https://github.com/GabboPenna/ha-engie-italia/issues/3).

## Procedura prevista

Occorrono HACS già configurato e Home Assistant 2026.9.0 o successivo.

1. Apri HACS, il menu in alto a destra e **Repository personalizzati**.
2. Inserisci `https://github.com/GabboPenna/ha-engie-italia`, scegli la categoria
   **Integrazione** e aggiungi il repository.
3. Apri **ENGIE Italia** e scarica la versione che intendi provare. Controlla
   versione, note e limiti: senza release HACS usa il ramo predefinito; un ramo
   di sviluppo presente in una PR non viene installato automaticamente.
4. Riavvia Home Assistant e segui la [guida al collegamento](SETUP.md).

Per passare da una copia manuale a HACS, la cartella del componente deve essere
la stessa: `custom_components/engie_italia`. Conserva la config entry dell'account;
la sessione risiede nel deposito privato HA, esterno alla cartella del componente.
Un aggiornamento non richiede intenzionalmente la cancellazione dell'account.

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

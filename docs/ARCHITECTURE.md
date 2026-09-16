# Architettura prevista

## Confini

Il nucleo `engie_italia` contiene solo modelli normalizzati e diagnostica
selezionata. Non conosce credenziali, HTTP o Home Assistant. Non e' ancora
un client ENGIE: nessun endpoint autenticato e' stato assunto o inventato.

Il futuro client asincrono avra' autenticazione e letture separate, timeout,
limiti di frequenza, richieste deduplicate e retry limitati. Una risposta
401 deve portare a rinnovo controllato o richiesta di riautenticazione;
429 e problemi di rete non devono generare cicli di login continui.

Le sole operazioni ammesse saranno autenticazione/rinnovo e lettura dei dati
verificati. Il verbo HTTP non e' una garanzia: una lettura Salesforce puo'
usare POST, percio' vanno consentite le singole operazioni note, non tutti i POST.
Non si implementeranno pagamenti, autoletture o modifiche alle forniture.

## Dati

- Ogni fornitura mantiene un'identita' distinta, anche con piu' POD/PDR.
- `None` significa valore assente; `Decimal('0')` e' uno zero realmente ricevuto.
- I valori vengono accettati solo dopo aver verificato il formato della sorgente.
  Una stringa localizzata non viene interpretata per tentativi.
- Gli intervalli richiedono un fuso orario e durata positiva in UTC.
- kWh, m3 e Smc restano distinti. Nessuna conversione gas implicita.
- Stato effettivo/stimato rimane sconosciuto se non dichiarato dalla sorgente.
- Serie duplicate, granularita' sovrapposte e rettifiche richiederanno una
  politica esplicita prima di qualsiasi aggregazione o importazione storica.

Il modello attuale non valida completezza o assenza di sovrapposizioni nelle
serie. Non usare la somma degli intervalli come totale fatturabile.

## Integrazione Home Assistant futura

Un solo `DataUpdateCoordinator` per account coordina gli aggiornamenti dei
sensori, evitando una richiesta separata per entita'. Un dispositivo per
fornitura e identificativi stabili evitano duplicati dopo una riconfigurazione.
La configurazione deve gestire autenticazione, riautenticazione e rimozione
senza file YAML contenenti credenziali. Il metodo dipende dal login verificato.

La diagnostica HA dovra' usare solo metadati approvati. Non includere payload
grezzi, identificativi, nomi, indirizzi o dati delle bollette nei log.
Il riepilogo attuale e' una allowlist per i modelli, non un filtro universale.

Per Energy non si usera' un totale mensile come se fosse un contatore cumulativo.
Importazione di statistiche storiche, timezone, rettifiche e doppio conteggio
con misuratori locali saranno verificati prima di attivare quella funzione.

Riferimenti:
- [Coordinamento dati HA](https://developers.home-assistant.io/docs/integration_fetching_data/)
- [Config flow HA](https://developers.home-assistant.io/docs/core/integration/config_flow/)
- [Diagnostica HA](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics/)
- [Requisiti HACS](https://www.hacs.xyz/docs/publish/integration/)

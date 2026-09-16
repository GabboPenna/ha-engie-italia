# Architettura prevista

## Confini

Modelli, diagnostica e parser restano indipendenti da HTTP e Home Assistant.
`mobile.py` interpreta forniture e consumi elettrici del servizio dell'app;
`portal.py` conserva il parser del portale. `client.py` aggiunge il trasporto
asincrono `aiohttp`, con credenziali fornite dal chiamante e nessuna persistenza.
Il probe pubblico usa il portale con login manuale; non e' il meccanismo di
autenticazione della futura integrazione mobile.

`PortalSupply` rappresenta soltanto l'identita', il tipo e lo stato osservato
di una fornitura. Rimane distinto da `SupplySnapshot`, che descrive intervalli
di consumo: nessuna lettura contrattuale genera misure energetiche implicite.

Il client attuale serializza letture e rinnovi, applica timeout e limiti sulle
risposte, vieta redirect e gestisce un solo rinnovo/retry dopo 401. Rispetta
`Retry-After` e non riprova rete/5xx in ciclo. Verifica gli errori applicativi
anche con HTTP 200. Cache, deduplicazione delle richieste identiche e pianificazione
restano responsabilita' del futuro coordinatore: nessun polling implicito per entita'.

Le sole operazioni ammesse sono rinnovo e lettura dei dati
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

Il parser mobile rifiuta duplicati e sovrapposizioni alla stessa granularita',
ma non presume completezza delle serie. Conserva i riepiloghi ENGIE separati
dai campioni: non usare la loro somma come totale fatturabile.
Dettaglio di autenticazione, errori, arrotondamenti e DST in [CLIENT.md](CLIENT.md).

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

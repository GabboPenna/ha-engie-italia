# Fatture e scadenze

Dalla beta **0.1.0b8** il dispositivo **Account / ENGIE Italia** espone il riepilogo
delle fatture. Le entità sono condivise fra le forniture dello stesso account.
Gli aggiornamenti seguono l'intervallo dell'integrazione, 6 ore per impostazione
predefinita, e il pulsante **Aggiorna dati**.

**Funzione sperimentale:** endpoint, parametri, campi e stati sono stati verificati
nel codice dell'app ENGIE 10.1.0 e coperti con dati sintetici. Nella prova del
16 settembre 2026 il servizio ha restituito HTTP 200, `code: OK`, nessuna fattura
e codici ENGIE `9` / `9.91`. Il significato preciso di `9.91` non è confermato:
questa risposta non dimostra l'assenza di fatture o debiti. Una risposta con
fatture reali resta da verificare; in presenza di questo codice i sensori dei
valori rimangono indisponibili e riprovano al normale aggiornamento.

## Sensori

I nomi delle entità dipendono dalla lingua e da eventuali rinomine in Home
Assistant. La chiave è il suffisso stabile dell'identificativo interno.

| Nome italiano | Chiave | Significato |
| --- | --- | --- |
| Dati fatture | `invoice_data_status` | Disponibili, nessuna fattura, dati incompleti o aggiornamento non riuscito. |
| Fatture disponibili | `invoices_count` | Numero di documenti distinti nella lista restituita, comprese le fatture pagate. |
| Fatture aperte | `open_invoices` | Numero di fatture non pagate, scadute o parzialmente pagate. |
| Totale da pagare | `outstanding_amount` | Somma in EUR degli importi **residui** delle fatture aperte. |
| Fatture scadute | `overdue_invoices` | Fatture aperte con stato scaduto o scadenza precedente alla data locale di HA. |
| Ultima fattura | `latest_invoice` | Numero fiscale della fattura con data di emissione più recente. |
| Importo ultima fattura | `latest_invoice_amount` | Importo originale in EUR, anche se già pagato. |
| Data ultima fattura | `latest_invoice_date` | Data di emissione comunicata da ENGIE. |
| Scadenza ultima fattura | `latest_invoice_due_date` | Scadenza dell'ultima fattura, anche se già pagata. |
| Prima scadenza aperta | `earliest_invoice_due_date` | Prima scadenza fra le fatture aperte; può essere già trascorsa. |
| Ultima sincronizzazione fatture | `invoices_last_sync` | Ultima lettura delle fatture completata senza errori; categoria diagnostica. |

## Come vengono calcolati i valori

La richiesta viene eseguita una volta per ogni contratto distinto presente
nell'account, anche se il contratto contiene sia luce sia gas. Non viene imposto
il limite alle ultime 1, 3 o 4 fatture: si usa il percorso della cronologia
dell'app. L'estensione storica effettiva dipende comunque da ciò che ENGIE
restituisce: il conteggio non promette lo storico completo della vita dell'account.

I documenti con lo stesso numero fiscale e gli stessi dati normalizzati sono
contati una sola volta. Duplicati discordanti fanno fallire l'aggiornamento,
senza scegliere arbitrariamente un importo. Se un contratto non è leggibile,
non viene mostrato un totale parziale dell'account.

Una fattura da 100 EUR con 25 EUR residui contribuisce al totale con **25 EUR**.
Il residuo mancante non viene sostituito con l'importo originale. Stati di
pagamento sconosciuti, residui negativi su fatture aperte o fatture dichiarate
pagate con residuo positivo lasciano sconosciuto il riepilogo dei debiti.
Eventuali importi negativi di documenti pagati sono conservati nel dettaglio
dell'ultima fattura, senza compensare arbitrariamente altri residui.

Una scadenza odierna non è ancora trascorsa. Le scadenze vengono rivalutate
all'aggiornamento dell'integrazione, non con un aggiornamento garantito a mezzanotte.
Se manca una data di emissione, non viene indovinata l'ultima fattura. A parità
di giorno, il numero fiscale ordina i documenti in modo deterministico: non
è disponibile l'orario di emissione.

Gli importi e i conteggi rappresentano la situazione letta: possono aumentare
o diminuire. Non sono contatori cumulativi e non alimentano la dashboard Energy.

## Distinguere zero, sconosciuto e indisponibile

- **Zero:** risposta valida senza fatture aperte. Una lista esplicitamente vuota
  e priva di errori produce zero per conteggi e residuo, senza inventare date.
- **Sconosciuto:** lettura riuscita ma un campo necessario è assente o ambiguo.
  I dati confermati restano utilizzabili; `Dati fatture` segnala dati incompleti.
- **Indisponibile:** richiesta fallita, manutenzione, errore ENGIE o struttura
  non valida. I vecchi importi non vengono ripubblicati come dati correnti.

Un errore delle fatture lascia disponibili i consumi che sono stati letti
correttamente. `Dati fatture` espone solo i codici numerici dell'errore, quando
presenti. La data di sincronizzazione precedente resta consultabile; al riavvio
non è ripristinata da un archivio privato delle fatture.

## Usarli nelle proprie automazioni

Per una notifica di nuova fattura, si può osservare il cambiamento dello **stato**
di `Ultima fattura`, escludendo i passaggi da o verso `unknown`, `unavailable`
e gli stati iniziali. Una variazione dell'importo o del pagamento dello stesso
documento non cambia il suo riferimento. `Fatture disponibili` è utile come
segnale aggiuntivo, ad esempio se arrivano più documenti nello stesso giorno.

È un riepilogo periodico, non una coda di eventi: più fatture fra due letture,
rettifiche o variazioni della cronologia possono produrre un solo cambiamento.
Per evitare notifiche ripetute sullo stesso documento, l'automazione può
conservare il riferimento già trattato e gestire riavvii e recupero da
indisponibilità. Questi sensori non garantiscono di rilevare ogni singolo
documento emesso fra due aggiornamenti.

Per promemoria, si possono usare `Fatture aperte`, `Totale da pagare`, `Fatture
scadute` e `Prima scadenza aperta`, verificando che i valori siano disponibili.
L'integrazione non crea automazioni, notifiche, pagamenti o download PDF.

Numeri, date e importi dei sensori possono finire nello storico di HA secondo
la configurazione di Recorder. Non sono inclusi nella diagnostica dell'integrazione.

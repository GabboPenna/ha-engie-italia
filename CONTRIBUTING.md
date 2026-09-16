# Contribuire

Aprire una issue prima di ampliare il perimetro. Il progetto e' in sola lettura:
non sono accettate funzioni per pagare, inviare autoletture o modificare contratti.

Distinguere sempre osservazioni verificate, ipotesi e funzionalita' pianificate.
Non aggiungere endpoint dedotti da integrazioni di altri Paesi senza verifica.

Prima di una pull request:

```sh
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
git diff --check
```

I test devono essere offline; i dati devono essere interamente sintetici.
Per modifiche all'integrazione eseguire anche `tests_ha` in un ambiente isolato
Python 3.14 con Home Assistant 2026.9.2, come descritto nel README.
Non usare credenziali in CI, non eseguire test contro account reali e non
allegare acquisizioni di rete. Consultare [SECURITY.md](SECURITY.md).

Ogni modifica ai modelli deve verificare anche che la diagnostica non esponga
nuovi dati. Eventuali parser dovranno gestire dati mancanti e campi inattesi
senza convertirli in consumi zero o identificativi di un'altra fornitura.

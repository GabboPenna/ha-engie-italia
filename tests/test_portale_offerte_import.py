import unittest

from tools.import_portale_offerte import (
    _merge_candidates,
    parse_candidate,
    short_offer_code,
)


def offer(
    *,
    commodity="E",
    client="01",
    price_type="01",
    bands="01",
    discount="",
):
    unit = "03" if commodity == "E" else "04"
    full_code = f"001714{commodity}SFML23XXDEMO0002300000000"
    return f"""
    <offerta>
      <IdentificativiOfferta>
        <PIVA_UTENTE>06289781004</PIVA_UTENTE>
        <COD_OFFERTA>{full_code}</COD_OFFERTA>
      </IdentificativiOfferta>
      <DettaglioOfferta>
        <TIPO_MERCATO>{"01" if commodity == "E" else "02"}</TIPO_MERCATO>
        <TIPO_CLIENTE>{client}</TIPO_CLIENTE>
        <TIPO_OFFERTA>{price_type}</TIPO_OFFERTA>
        <NOME_OFFERTA>Invented offer</NOME_OFFERTA>
        <DURATA>24</DURATA>
      </DettaglioOfferta>
      <ValiditaOfferta>
        <DATA_INIZIO>01/02/2025_00:00:00</DATA_INIZIO>
        <DATA_FINE>28/02/2025_23:59:59</DATA_FINE>
      </ValiditaOfferta>
      <TipoPrezzo><TIPOLOGIA_FASCE>{bands}</TIPOLOGIA_FASCE></TipoPrezzo>
      <ComponenteImpresa>
        <MACROAREA>01</MACROAREA>
        <IntervalloPrezzi><PREZZO>60.00</PREZZO><UNITA_MISURA>01</UNITA_MISURA></IntervalloPrezzi>
      </ComponenteImpresa>
      <ComponenteImpresa>
        <MACROAREA>04</MACROAREA>
        <IntervalloPrezzi><FASCIA_COMPONENTE>01</FASCIA_COMPONENTE><PREZZO>0.10000</PREZZO><UNITA_MISURA>{unit}</UNITA_MISURA></IntervalloPrezzi>
      </ComponenteImpresa>
      <ComponenteImpresa>
        <MACROAREA>04</MACROAREA>
        <IntervalloPrezzi><FASCIA_COMPONENTE>01</FASCIA_COMPONENTE><PREZZO>0.02000</PREZZO><UNITA_MISURA>{unit}</UNITA_MISURA></IntervalloPrezzi>
      </ComponenteImpresa>
      {discount}
    </offerta>
    """.encode()


class PortaleOfferteImportTests(unittest.TestCase):
    def test_standard_code_is_recovered_without_using_the_offer_name(self):
        self.assertEqual(
            short_offer_code("001714ESFML23XXDEMO0002300000000"), "DEMO#00023"
        )
        self.assertIsNone(short_offer_code("legacy-code"))

    def test_simple_electricity_and_gas_rates_are_independent(self):
        power = parse_candidate(offer(), "https://example.invalid/power.xml")
        gas = parse_candidate(offer(commodity="G"), "https://example.invalid/gas.xml")
        self.assertTrue(power.eligible)
        self.assertTrue(gas.eligible)
        self.assertEqual(power.commodity, "electricity")
        self.assertEqual(gas.commodity, "gas")
        self.assertEqual(power.rate["unit_price"], "0.12000")
        self.assertEqual(gas.rate["unit_price"], "0.12000")
        self.assertEqual(power.rate["duration_months"], 24)
        self.assertIsNone(power.rate["network_losses_included"])
        self.assertIsNone(gas.rate["reference_pcs_gj_smc"])

    def test_complex_or_non_domestic_offers_are_not_imported_partially(self):
        samples = (
            offer(client="02"),
            offer(price_type="02"),
            offer(bands="03"),
            offer(discount="<Sconto><TIPOLOGIA>03</TIPOLOGIA></Sconto>"),
        )
        for sample in samples:
            with self.subTest(sample=sample):
                candidate = parse_candidate(sample, "https://example.invalid/data.xml")
                self.assertFalse(candidate.eligible)
                self.assertIsNone(candidate.rate)

    def test_tiered_components_are_rejected(self):
        sample = offer().replace(
            b"<PREZZO>0.10000</PREZZO>",
            b"<CONSUMO_DA>0</CONSUMO_DA><PREZZO>0.10000</PREZZO>",
            1,
        )
        candidate = parse_candidate(sample, "https://example.invalid/data.xml")
        self.assertFalse(candidate.eligible)
        self.assertIn("tiered or time-limited component", candidate.reasons)

    def test_unsupported_component_units_are_not_treated_as_zero(self):
        sample = offer().replace(
            b"<UNITA_MISURA>01</UNITA_MISURA>",
            b"<UNITA_MISURA>02</UNITA_MISURA>",
            1,
        )
        candidate = parse_candidate(sample, "https://example.invalid/data.xml")
        self.assertFalse(candidate.eligible)
        self.assertIn("unsupported component unit", candidate.reasons)

    def test_only_superset_window_updates_with_identical_terms_are_merged(self):
        first = parse_candidate(offer(), "https://example.invalid/first.xml")
        extended = parse_candidate(
            offer().replace(b"28/02/2025", b"07/03/2025"),
            "https://example.invalid/extended.xml",
        )
        merged = _merge_candidates(first, extended)
        self.assertEqual(merged.rate["offered_until"], "2025-03-07")
        self.assertEqual(
            merged.rate["source_url"], "https://example.invalid/extended.xml"
        )

        changed = parse_candidate(
            offer().replace(b"0.10000", b"0.10001"),
            "https://example.invalid/changed.xml",
        )
        self.assertIsNone(_merge_candidates(first, changed))


if __name__ == "__main__":
    unittest.main()

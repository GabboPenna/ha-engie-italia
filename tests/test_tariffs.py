import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from tariff_fixtures import catalog, tariff_supplies

from engie_italia import tariffs
from engie_italia.mobile import parse_mobile_supplies
from engie_italia.portal import SupplyStatus

TODAY = date(2025, 3, 11)


class TariffTests(unittest.TestCase):
    def setUp(self):
        self.catalog = patch.object(tariffs, "VERIFIED_TARIFFS", catalog(tariffs))
        self.catalog.start()
        self.addCleanup(self.catalog.stop)
        self.power, self.gas = parse_mobile_supplies(tariff_supplies())

    def test_exact_version_and_commodity_select_separate_prices(self):
        power = tariffs.current_tariff(self.power, TODAY)
        gas = tariffs.current_tariff(self.gas, TODAY)
        self.assertEqual(
            (power.unit_price, power.annual_fee, power.unit),
            (Decimal("0.12345"), Decimal("65"), "EUR/kWh"),
        )
        self.assertEqual(
            (gas.unit_price, gas.annual_fee, gas.unit),
            (Decimal("0.56789"), Decimal("75"), "EUR/Smc"),
        )
        self.assertTrue(power.network_losses_included)
        self.assertEqual(gas.reference_pcs_gj_smc, Decimal("0.03999"))
        # The public subscription window has ended; the personal terms have not.
        self.assertEqual(tariffs.tariff_status(self.power, TODAY), "verified")

    def test_same_name_and_family_do_not_match_another_version(self):
        data = tariff_supplies()
        data["listaContratti"][0]["forniture"][0]["prodottoCodiceUnivoco"] = (
            "SYNTHETIC#00124"
        )
        power = parse_mobile_supplies(data)[0]
        self.assertIsNone(tariffs.current_tariff(power, TODAY))
        self.assertEqual(tariffs.tariff_status(power, TODAY), "unverified_offer")

    def test_missing_or_malformed_optional_metadata_keeps_supplies(self):
        original = tariff_supplies()["listaContratti"][0]["forniture"][0]
        keys = (
            "productCode",
            "prodottoCodiceUnivoco",
            "priceType",
            "tipoContratto",
            "inizioCE",
            "fineCE",
            "durataCE",
        )
        for key in keys:
            for value in (None, [], {}, True):
                data = tariff_supplies()
                data["listaContratti"][0]["forniture"][0][key] = value
                with self.subTest(key=key, value=value):
                    power, gas = parse_mobile_supplies(data)
                    self.assertIsNone(power.offer)
                    self.assertIsNone(tariffs.current_tariff(power, TODAY))
                    self.assertEqual(power.supply_id, original["id"])
                    self.assertIsNotNone(tariffs.current_tariff(gas, TODAY))

    def test_invalid_dates_and_conflicting_product_codes_are_rejected(self):
        for key, value in (
            ("inizioCE", "2025-02-30"),
            ("fineCE", "2025-02-28"),
            ("fineCE", "20260228"),
            ("productCode", "DIFFERENT"),
            ("durataCE", 0),
            ("durataCE", "12"),
        ):
            data = tariff_supplies()
            data["listaContratti"][0]["forniture"][0][key] = value
            with self.subTest(key=key, value=value):
                self.assertIsNone(parse_mobile_supplies(data)[0].offer)

    def test_validity_boundaries_do_not_extrapolate_prices(self):
        for day, status in (
            (date(2025, 2, 28), "not_yet_valid"),
            (date(2025, 3, 1), "verified"),
            (date(2026, 2, 28), "verified"),
            (date(2026, 3, 1), "expired"),
        ):
            with self.subTest(day=day):
                self.assertEqual(tariffs.tariff_status(self.power, day), status)
                self.assertEqual(
                    tariffs.current_tariff(self.power, day) is not None,
                    status == "verified",
                )

    def test_renewed_dates_with_unchanged_code_do_not_reuse_initial_price(self):
        power = replace(
            self.power,
            offer=replace(
                self.power.offer,
                valid_from=date(2026, 3, 1),
                valid_until=date(2027, 2, 28),
            ),
        )
        self.assertEqual(
            tariffs.tariff_status(power, date(2026, 3, 2)), "unverified_renewal"
        )
        self.assertIsNone(tariffs.current_tariff(power, date(2026, 3, 2)))

    def test_unsupported_terms_never_become_zero_prices(self):
        for change in (
            {"price_type": "INDEXED"},
            {"contract_type": "Non domestico"},
            {"contract_type": "unknown"},
            {"duration_months": 24},
            {"valid_until": date(2027, 2, 28)},
        ):
            power = replace(self.power, offer=replace(self.power.offer, **change))
            with self.subTest(change=change):
                self.assertEqual(
                    tariffs.tariff_status(power, TODAY), "unsupported_terms"
                )
                self.assertIsNone(tariffs.current_tariff(power, TODAY))

    def test_inactive_supply_and_unknown_activation_have_no_price(self):
        power = replace(self.power, status=SupplyStatus.UNKNOWN)
        self.assertEqual(tariffs.tariff_status(power, TODAY), "inactive")
        data = tariff_supplies()
        data["listaContratti"][0]["forniture"][1]["dataAttivazione"] = None
        for supply in parse_mobile_supplies(data):
            self.assertIsNone(tariffs.current_tariff(supply, TODAY))

    def test_dual_supply_uses_first_activation_and_waits_for_second_activation(self):
        data = tariff_supplies()
        data["listaContratti"][0]["forniture"][1]["dataAttivazione"] = "2025-04-01"
        power, gas = parse_mobile_supplies(data)
        self.assertEqual(tariffs.tariff_status(power, TODAY), "verified")
        self.assertEqual(tariffs.tariff_status(gas, TODAY), "not_yet_valid")
        self.assertEqual(tariffs.tariff_status(gas, date(2025, 4, 1)), "verified")

    def test_offer_metadata_is_not_in_supply_repr(self):
        text = repr((self.power, self.gas))
        for private in ("SYNTHETIC", "2025-03-01", "residente", "synthetic"):
            self.assertNotIn(private, text)

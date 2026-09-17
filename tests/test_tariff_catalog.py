import json
import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tariff_fixtures import catalog, catalog_data, tariff_supplies

from engie_italia import tariff_catalog, tariffs
from engie_italia.mobile import parse_mobile_supplies
from engie_italia.tariff_catalog import CatalogValidationError, parse_tariff_catalog


class TariffCatalogTests(unittest.TestCase):
    def test_parsing_preserves_prices_precision_and_immutable_models(self):
        result = parse_tariff_catalog(json.dumps(catalog_data()))
        self.assertEqual(result, catalog(tariffs))
        rate = result["SYNTHETIC#00123"].electricity
        self.assertEqual(str(rate.annual_fee), "65.00")
        with self.assertRaises(TypeError):
            result["SYNTHETIC#00124"] = result["SYNTHETIC#00123"]
        with self.assertRaises(FrozenInstanceError):
            rate.unit_price = Decimal("0")

    def test_duplicate_offer_codes_and_nested_fields_are_rejected(self):
        raw = json.dumps(catalog_data())
        offer = json.dumps(catalog_data()["offers"]["SYNTHETIC#00123"])
        for duplicate in (
            raw.replace(
                '"schema_version": 1', '"schema_version": 1, "schema_version": 1'
            ),
            raw.replace(
                '"unit_price": "0.12345"',
                '"unit_price": "0.9", "unit_price": "0.12345"',
            ),
            '{"schema_version": 1, "offers": {'
            f'"SYNTHETIC#00123": {offer}, "SYNTHETIC#00123": {offer}'
            "}}",
        ):
            with self.subTest(raw=duplicate):
                with self.assertRaisesRegex(
                    CatalogValidationError, "duplicate JSON key"
                ):
                    parse_tariff_catalog(duplicate)

    def test_invalid_json_schema_and_empty_catalogue_fail_validation(self):
        for raw in ("{", "[]", "null", "{}", '{"schema_version": 1, "offers": {}}'):
            with self.subTest(raw=raw), self.assertRaises(CatalogValidationError):
                parse_tariff_catalog(raw)
        for version in (True, 1.0, "1", 2, None):
            data = catalog_data()
            data["schema_version"] = version
            with (
                self.subTest(version=version),
                self.assertRaises(CatalogValidationError),
            ):
                parse_tariff_catalog(json.dumps(data))

    def test_missing_or_unknown_fields_at_each_level_are_rejected(self):
        for path, key in (
            ((), "offers"),
            (("offers", "SYNTHETIC#00123"), "gas"),
            (("offers", "SYNTHETIC#00123", "electricity"), "network_losses_included"),
            (("offers", "SYNTHETIC#00123", "gas"), "reference_pcs_gj_smc"),
        ):
            for missing in (True, False):
                data = catalog_data()
                target = data
                for segment in path:
                    target = target[segment]
                if missing:
                    del target[key]
                else:
                    target["unexpected_field"] = True
                with self.subTest(path=path, missing=missing):
                    with self.assertRaises(CatalogValidationError):
                        parse_tariff_catalog(json.dumps(data))

    def test_decimal_fields_reject_ambiguous_values_but_accept_explicit_zero(self):
        for field in ("unit_price", "annual_fee"):
            for value in (
                0.1,
                0,
                True,
                None,
                "-0.1",
                "NaN",
                "Infinity",
                "1e-2",
                "0,1",
                " 0.1",
                "01",
                [],
            ):
                data = catalog_data()
                data["offers"]["SYNTHETIC#00123"]["electricity"][field] = value
                with self.subTest(field=field, value=value):
                    with self.assertRaises(CatalogValidationError):
                        parse_tariff_catalog(json.dumps(data))
            data["offers"]["SYNTHETIC#00123"]["electricity"][field] = "0.00"
            rate = parse_tariff_catalog(json.dumps(data))["SYNTHETIC#00123"].electricity
            self.assertEqual(getattr(rate, field), Decimal("0"))

    def test_units_losses_and_pcs_cannot_be_silently_misinterpreted(self):
        for utility, key, value in (
            ("electricity", "unit", "EUR/Smc"),
            ("gas", "unit", "EUR/m3"),
            ("electricity", "network_losses_included", "true"),
            ("electricity", "network_losses_included", 1),
            ("gas", "reference_pcs_gj_smc", "0"),
            ("gas", "reference_pcs_gj_smc", None),
        ):
            data = catalog_data()
            data["offers"]["SYNTHETIC#00123"][utility][key] = value
            with self.subTest(utility=utility, key=key, value=value):
                with self.assertRaises(CatalogValidationError):
                    parse_tariff_catalog(json.dumps(data))

    def test_offer_codes_dates_and_source_references_are_required(self):
        for key, value in (
            ("source_url", "http://example.invalid/terms.pdf"),
            ("source_url", "https:///terms.pdf"),
            ("source_url", "https://user:password@example.invalid/terms.pdf"),
            ("source_sha256", "not-a-digest"),
            ("offered_from", "2025-02-30"),
            ("offered_from", "2025-01-09"),
            ("offered_until", "20250108"),
        ):
            data = catalog_data()
            data["offers"]["SYNTHETIC#00123"][key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(CatalogValidationError):
                    parse_tariff_catalog(json.dumps(data))
        for code in ("SYNTHETIC", "SYNTHETIC#123", "synthetic#00123"):
            data = catalog_data()
            data["offers"][code] = data["offers"].pop("SYNTHETIC#00123")
            with self.subTest(code=code), self.assertRaises(CatalogValidationError):
                parse_tariff_catalog(json.dumps(data))

    def test_package_resource_loads_synthetic_catalogue(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data/tariffs.json").write_text(
                json.dumps(catalog_data()), encoding="utf-8"
            )
            with patch.object(tariff_catalog, "files", return_value=root):
                self.assertEqual(tariff_catalog.load_tariff_catalog(), catalog(tariffs))

    def test_bad_catalogue_disables_prices_without_breaking_supply_parsing(self):
        for error in (
            FileNotFoundError("missing catalog"),
            CatalogValidationError("invalid JSON"),
        ):
            with patch.object(tariffs, "load_tariff_catalog", side_effect=error):
                with self.assertLogs(tariffs.__name__, level="ERROR"):
                    result = tariffs._load_verified_tariffs()
            self.assertEqual(result, {})
            with patch.object(tariffs, "VERIFIED_TARIFFS", result):
                supplies = parse_mobile_supplies(tariff_supplies())
                self.assertEqual(len(supplies), 2)
                for supply in supplies:
                    self.assertEqual(
                        tariffs.tariff_status(supply, supply.activation_date),
                        "unverified_offer",
                    )

    def test_validator_exit_status_distinguishes_good_and_bad_catalogues(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            for raw, exit_code in ((json.dumps(catalog_data()), 0), ("{", 1)):
                path.write_text(raw, encoding="utf-8")
                with (
                    patch("sys.argv", ["tariff_catalog", str(path)]),
                    patch("sys.stdout"),
                    patch("sys.stderr"),
                ):
                    if exit_code:
                        with self.assertRaises(SystemExit) as result:
                            tariff_catalog.main()
                        self.assertEqual(result.exception.code, exit_code)
                    else:
                        tariff_catalog.main()

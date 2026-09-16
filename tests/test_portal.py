"""Entirely invented fixtures matching only the observed supply field structure."""

import json
import unittest
from dataclasses import asdict

from engie_italia.diagnostics import portal_summary
from engie_italia.models import Utility
from engie_italia.portal import (
    PortalPayloadError,
    PortalSupply,
    SupplyStatus,
    parse_dashboard_supplies,
)


def supply(commodity="Luce", identifier="synthetic-power", status="attiva"):
    return {"id": identifier, "commodity": commodity, "statoCalc": status}


def dashboard(*supplies):
    return {"contractChains": {"synthetic-chain": {"forniture": list(supplies)}}}


class PortalTests(unittest.TestCase):
    def test_dual_fuel_contract_yields_two_distinct_supplies(self):
        result = parse_dashboard_supplies(
            dashboard(supply(), supply("Gas", "synthetic-gas"))
        )
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].supply_id, "synthetic-power")
        self.assertIs(result[0].utility, Utility.ELECTRICITY)
        self.assertIs(result[1].utility, Utility.GAS)
        self.assertTrue(all(s.status is SupplyStatus.ACTIVE for s in result))

    def test_all_contract_chains_are_processed(self):
        payload = dashboard(supply())
        payload["contractChains"]["another-synthetic-chain"] = {
            "forniture": [supply("Gas", "synthetic-gas")]
        }
        self.assertEqual(len(parse_dashboard_supplies(payload)), 2)

    def test_explicit_empty_account_is_distinct_from_missing_data(self):
        self.assertEqual(parse_dashboard_supplies({"contractChains": {}}), ())
        self.assertEqual(parse_dashboard_supplies(dashboard()), ())
        for payload in (None, [], {}, {"contractChains": None}, {"contractChains": []}):
            with self.subTest(payload=payload), self.assertRaises(PortalPayloadError):
                parse_dashboard_supplies(payload)

    def test_invalid_chain_or_supply_fails_without_partial_success(self):
        for chain in (None, [], {}, {"forniture": {}}, {"forniture": None}):
            with self.subTest(chain=chain), self.assertRaises(PortalPayloadError):
                parse_dashboard_supplies({"contractChains": {"synthetic": chain}})
        for raw in (None, [], "invalid"):
            with self.subTest(raw=raw), self.assertRaises(PortalPayloadError):
                parse_dashboard_supplies(dashboard(supply(), raw))

    def test_unknown_status_is_not_assumed_active_or_inactive(self):
        for status in (None, "", "new-provider-status", 1):
            with self.subTest(status=status):
                result = parse_dashboard_supplies(dashboard(supply(status=status)))
                self.assertIs(result[0].status, SupplyStatus.UNKNOWN)

    def test_missing_status_remains_unknown(self):
        raw = supply()
        del raw["statoCalc"]
        self.assertIs(
            parse_dashboard_supplies(dashboard(raw))[0].status, SupplyStatus.UNKNOWN
        )

    def test_unknown_commodity_is_not_guessed(self):
        for commodity in (None, "Water", "electricity", {}, [], True):
            with (
                self.subTest(commodity=commodity),
                self.assertRaises(PortalPayloadError),
            ):
                parse_dashboard_supplies(dashboard(supply(commodity=commodity)))

    def test_missing_or_invalid_identifier_is_rejected(self):
        for identifier in (None, "", "  ", 42, True, []):
            with (
                self.subTest(identifier=identifier),
                self.assertRaises(PortalPayloadError),
            ):
                parse_dashboard_supplies(dashboard(supply(identifier=identifier)))

    def test_duplicate_identifiers_are_not_silently_merged(self):
        with self.assertRaisesRegex(PortalPayloadError, "Duplicate"):
            parse_dashboard_supplies(dashboard(supply(), supply()))

    def test_sensitive_and_unverified_fields_are_not_retained(self):
        raw = supply()
        raw.update({"punto": {"pod": "synthetic-pod", "potenzaConsumo": 3.3}})
        payload = dashboard(raw)
        payload.update({"info": {"email": "synthetic@example.invalid"}, "cards": []})
        result = parse_dashboard_supplies(payload)
        self.assertEqual(set(asdict(result[0])), {"supply_id", "utility", "status"})
        output = json.dumps(portal_summary(result))
        for private in (
            "synthetic-power",
            "synthetic-pod",
            "synthetic@example.invalid",
        ):
            self.assertNotIn(private, output)
            self.assertNotIn(private, repr(result))

    def test_supplies_do_not_fabricate_consumption_data(self):
        result = parse_dashboard_supplies(dashboard(supply("Gas", "synthetic-gas")))
        self.assertFalse(hasattr(result[0], "intervals"))
        self.assertEqual(
            portal_summary(result),
            {"schema_version": 1, "supplies": [{"utility": "gas", "status": "active"}]},
        )

    def test_errors_do_not_echo_account_values(self):
        for payload in (
            dashboard(supply(commodity="synthetic-sensitive-data")),
            dashboard(
                supply(identifier="synthetic-secret"),
                supply(identifier="synthetic-secret"),
            ),
        ):
            with self.assertRaises(PortalPayloadError) as raised:
                parse_dashboard_supplies(payload)
            self.assertNotIn("synthetic", str(raised.exception))

    def test_metadata_constructor_requires_normalized_enums(self):
        with self.assertRaises(PortalPayloadError):
            PortalSupply("synthetic", "Luce", SupplyStatus.ACTIVE)
        with self.assertRaises(PortalPayloadError):
            PortalSupply("synthetic", Utility.ELECTRICITY, "attiva")


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from engie_italia.diagnostics import diagnostic_summary
from engie_italia.models import (
    ConsumptionInterval,
    Quality,
    SupplySnapshot,
    Unit,
    Utility,
)


class DiagnosticTests(unittest.TestCase):
    def test_empty_account_is_supported(self):
        self.assertEqual(diagnostic_summary([]), {"schema_version": 1, "supplies": []})

    def test_diagnostics_exclude_identifiers_quantities_and_dates(self):
        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = start + timedelta(hours=1)
        snapshot = SupplySnapshot(
            "synthetic-private-identifier",
            Utility.ELECTRICITY,
            (ConsumptionInterval(start, end, Decimal("9876.54321"), Unit.KWH),),
            end,
        )
        summary = diagnostic_summary([snapshot])
        encoded = json.dumps(summary)
        for private in (snapshot.supply_id, "9876.54321", "2026"):
            self.assertNotIn(private, encoded)
        self.assertEqual(
            set(summary["supplies"][0]),
            {
                "utility",
                "interval_count",
                "missing_value_count",
                "estimated_value_count",
                "units",
            },
        )

    def test_missing_and_estimated_values_are_counted_separately(self):
        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = start + timedelta(hours=1)
        snapshot = SupplySnapshot(
            "synthetic-gas",
            Utility.GAS,
            (
                ConsumptionInterval(start, end, None, Unit.CUBIC_METERS),
                ConsumptionInterval(
                    end,
                    end + timedelta(hours=1),
                    Decimal("0"),
                    Unit.CUBIC_METERS,
                    Quality.ESTIMATED,
                ),
            ),
            end,
        )
        result = diagnostic_summary([snapshot])["supplies"][0]
        self.assertEqual(result["interval_count"], 2)
        self.assertEqual(result["missing_value_count"], 1)
        self.assertEqual(result["estimated_value_count"], 1)


if __name__ == "__main__":
    unittest.main()

"""Synthetic values only; no provider account or captured responses."""

import unittest
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from engie_italia.models import (
    ConsumptionInterval,
    Quality,
    SupplySnapshot,
    Unit,
    Utility,
    consumption_value,
)

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(hours=1)


def interval(value=None, unit=Unit.KWH, quality=Quality.UNKNOWN):
    return ConsumptionInterval(START, END, value, unit, quality)


class ValueTests(unittest.TestCase):
    def test_missing_stays_missing(self):
        self.assertIsNone(consumption_value(None))

    def test_zero_is_valid_and_distinct_from_missing(self):
        self.assertEqual(consumption_value(0), Decimal("0"))
        self.assertIsNotNone(consumption_value(0))

    def test_machine_values_preserve_decimal_precision(self):
        for raw in ("12.345", Decimal("12.345"), 12.345):
            with self.subTest(raw=raw):
                self.assertEqual(consumption_value(raw), Decimal("12.345"))

    def test_invalid_values_are_not_silently_zero(self):
        for raw in (
            "",
            "unknown",
            "unavailable",
            "NaN",
            "Infinity",
            "-1",
            "1,234",
            "1.234,5",
            True,
            False,
            [],
            {},
            float("inf"),
            float("nan"),
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                consumption_value(raw)


class IntervalTests(unittest.TestCase):
    def test_quality_is_unknown_unless_provided(self):
        self.assertIs(interval(Decimal("1")).quality, Quality.UNKNOWN)

    def test_actual_and_estimated_remain_distinct(self):
        self.assertNotEqual(
            interval(Decimal("1"), quality=Quality.ACTUAL),
            interval(Decimal("1"), quality=Quality.ESTIMATED),
        )

    def test_nonpositive_period_is_rejected(self):
        for end in (START, START - timedelta(seconds=1)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                ConsumptionInterval(START, end, None, Unit.KWH)

    def test_naive_timestamps_are_rejected(self):
        with self.assertRaises(ValueError):
            ConsumptionInterval(START.replace(tzinfo=None), END, None, Unit.KWH)

    def test_interval_requires_normalized_values_and_units(self):
        with self.assertRaises(ValueError):
            interval(1.5)
        with self.assertRaises(ValueError):
            interval(Decimal("NaN"))
        with self.assertRaises(ValueError):
            interval(unit="kWh")
        with self.assertRaises(ValueError):
            interval(quality="actual")

    def test_duration_uses_elapsed_time_across_offset_change(self):
        start = datetime(2026, 10, 25, 2, tzinfo=timezone(timedelta(hours=2)))
        end = datetime(2026, 10, 25, 2, tzinfo=timezone(timedelta(hours=1)))
        self.assertEqual(
            ConsumptionInterval(start, end, None, Unit.KWH).duration,
            timedelta(hours=1),
        )

    def test_repeated_local_hour_is_valid_for_the_same_timezone(self):
        try:
            zone = ZoneInfo("Europe/Rome")
        except ZoneInfoNotFoundError:
            self.skipTest("System timezone database unavailable")
        start = datetime(2026, 10, 25, 2, tzinfo=zone, fold=0)
        end = datetime(2026, 10, 25, 2, tzinfo=zone, fold=1)
        self.assertEqual(
            ConsumptionInterval(start, end, None, Unit.KWH).duration,
            timedelta(hours=1),
        )


class SupplyTests(unittest.TestCase):
    def test_electricity_with_values_and_gas_without_values_can_coexist(self):
        power = SupplySnapshot(
            "synthetic-power", Utility.ELECTRICITY, (interval(Decimal("2")),), END
        )
        gas = SupplySnapshot("synthetic-gas", Utility.GAS, (), END)
        self.assertEqual(power.intervals[0].value, Decimal("2"))
        self.assertEqual(gas.intervals, ())

    def test_missing_gas_interval_does_not_become_zero(self):
        gas = SupplySnapshot(
            "synthetic-gas", Utility.GAS, (interval(unit=Unit.CUBIC_METERS),), END
        )
        self.assertIsNone(gas.intervals[0].value)

    def test_gas_units_are_not_converted(self):
        for unit in (Unit.CUBIC_METERS, Unit.STANDARD_CUBIC_METERS):
            gas = SupplySnapshot(
                "synthetic-gas", Utility.GAS, (interval(Decimal("2"), unit),), END
            )
            self.assertIs(gas.intervals[0].unit, unit)

    def test_utility_unit_mismatch_is_rejected(self):
        for utility, unit in (
            (Utility.GAS, Unit.KWH),
            (Utility.ELECTRICITY, Unit.CUBIC_METERS),
        ):
            with self.subTest(utility=utility), self.assertRaises(ValueError):
                SupplySnapshot("synthetic", utility, (interval(unit=unit),), END)

    def test_invalid_supply_metadata_is_rejected(self):
        with self.assertRaises(ValueError):
            SupplySnapshot(" ", Utility.GAS, (), END)
        with self.assertRaises(ValueError):
            SupplySnapshot("synthetic", "gas", (), END)
        with self.assertRaises(ValueError):
            SupplySnapshot("synthetic", Utility.GAS, [], END)
        with self.assertRaises(ValueError):
            SupplySnapshot("synthetic", Utility.GAS, (), END.replace(tzinfo=None))

    def test_identifier_is_not_in_representation(self):
        self.assertNotIn(
            "synthetic-sensitive-id",
            repr(SupplySnapshot("synthetic-sensitive-id", Utility.GAS, (), END)),
        )


if __name__ == "__main__":
    unittest.main()

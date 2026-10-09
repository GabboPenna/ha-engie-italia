import copy
import json
import unittest
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from mobile_fixtures import daily, gas_update, hourly, monthly_gas, sample, supplies

from engie_italia.diagnostics import diagnostic_summary
from engie_italia.errors import PayloadError, ServiceError
from engie_italia.mobile import (
    Granularity,
    ServiceStatus,
    parse_account_metadata,
    parse_daily_electricity,
    parse_gas_last_update,
    parse_hourly_electricity,
    parse_mobile_supplies,
    parse_monthly_gas,
    successful_payload,
)
from engie_italia.models import Quality, Unit, Utility
from engie_italia.portal import SupplyStatus

CONTEXT = {
    "supply_id": "synthetic-sensitive-id",
    "fetched_at": datetime(2025, 11, 1, tzinfo=UTC),
}


class MobileSuppliesTests(unittest.TestCase):
    def test_dual_fuel_and_actual_contract_code_mapping(self):
        power, gas = parse_mobile_supplies(supplies())
        self.assertIs(power.utility, Utility.ELECTRICITY)
        self.assertIs(gas.utility, Utility.GAS)
        self.assertEqual(power.contract_id, "synthetic-contract")
        self.assertEqual(power.point_id, "synthetic-pod")
        self.assertEqual(gas.point_id, "synthetic-pdr")
        self.assertIs(power.status, SupplyStatus.ACTIVE)
        self.assertEqual(power.contracted_power, Decimal("3"))
        self.assertEqual(power.available_power, Decimal("3.3"))
        self.assertEqual(gas.self_reading_window_start, date(2025, 4, 10))
        self.assertEqual(gas.self_reading_window_end, date(2025, 4, 20))

    def test_optional_account_services_are_normalized_without_private_fields(self):
        result = parse_account_metadata(supplies())
        self.assertEqual(result.next_bill_date, date(2025, 4, 15))
        self.assertIs(result.direct_debit, ServiceStatus.ACTIVE)
        self.assertIs(result.digital_bill, ServiceStatus.ACTIVE)
        self.assertNotIn("private", repr(result))

    def test_mixed_and_malformed_optional_metadata_stays_safe(self):
        data = supplies()
        second = copy.deepcopy(data["listaContratti"][0])
        second["codContr"] = "synthetic-contract-2"
        second["dataProxBol"] = ["not-a-date"]
        second["sdd"]["stato"] = "n"
        second["bol"] = None
        second["forniture"] = []
        data["listaContratti"].append(second)
        result = parse_account_metadata(data)
        self.assertEqual(result.next_bill_date, date(2025, 4, 15))
        self.assertIs(result.direct_debit, ServiceStatus.MIXED)
        self.assertIs(result.digital_bill, ServiceStatus.UNKNOWN)

        data["listaContratti"][0]["forniture"][0]["punto"].update(
            potenzaImpegnata=True,
            potenzaConsumo=-1,
        )
        data["listaContratti"][0]["forniture"][1]["autolettura"].update(
            inizioFinestra="2025-04-30",
            fineFinestra="2025-04-01",
        )
        power, gas = parse_mobile_supplies(data)
        self.assertIsNone(power.contracted_power)
        self.assertIsNone(power.available_power)
        self.assertIsNone(gas.self_reading_window_start)
        self.assertIsNone(gas.self_reading_window_end)

    def test_identifiers_are_not_in_repr_and_unneeded_data_is_dropped(self):
        result = parse_mobile_supplies(supplies())
        self.assertNotIn("synthetic", repr(result))
        self.assertFalse(hasattr(result[0], "sdd"))

    def test_explicit_empty_account_is_not_a_missing_response(self):
        self.assertEqual(
            parse_mobile_supplies({"code": "OK", "listaContratti": []}), ()
        )
        for value in (None, {}, True, "wrong"):
            with self.subTest(value=value), self.assertRaises(PayloadError):
                parse_mobile_supplies({"code": "OK", "listaContratti": value})

    def test_unknown_activity_is_not_assumed_active(self):
        for value in (None, "n", "new", True, 1):
            data = supplies()
            data["listaContratti"][0]["forniture"][0]["attiva"] = value
            self.assertIs(parse_mobile_supplies(data)[0].status, SupplyStatus.UNKNOWN)

    def test_invalid_supply_does_not_yield_partial_data(self):
        for key, value in (
            ("id", ""),
            ("id", False),
            ("punto", {}),
            ("commodity", "water"),
            ("commodity", []),
            ("dataAttivazione", False),
            ("dataAttivazione", "2025-02-30"),
        ):
            data = supplies()
            data["listaContratti"][0]["forniture"][1][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(PayloadError):
                parse_mobile_supplies(data)

    def test_duplicate_supplies_rejected(self):
        data = supplies()
        data["listaContratti"].append(copy.deepcopy(data["listaContratti"][0]))
        with self.assertRaises(PayloadError):
            parse_mobile_supplies(data)


class ElectricityTests(unittest.TestCase):
    def test_daily_values_units_timezone_and_independent_totals(self):
        result = parse_daily_electricity(daily(), **CONTEXT)
        self.assertIs(result.granularity, Granularity.DAY)
        interval = result.snapshot.intervals[0]
        self.assertEqual(interval.value, Decimal("1.25"))
        self.assertIs(interval.unit, Unit.KWH)
        self.assertIs(interval.quality, Quality.ACTUAL)
        self.assertEqual(interval.start.hour, 0)
        self.assertEqual(interval.start.tzinfo.key, "Europe/Rome")
        self.assertEqual(interval.duration, timedelta(days=1))
        self.assertEqual(result.month_totals[0].value, Decimal("7.31"))
        self.assertEqual(result.year_totals[0].value, Decimal("21.37"))

    def test_quality_missing_and_true_zero_are_distinct(self):
        rows = [
            sample("2025-03-10", 0),
            sample("2025-03-11", 0, "NOT_PROVIDED"),
            sample("2025-03-12", 1.1, "estimated"),
            sample("2025-03-13", 0.4, "new-type"),
        ]
        result = parse_daily_electricity(daily(rows=rows), **CONTEXT).snapshot.intervals
        self.assertEqual(result[0].value, Decimal(0))
        self.assertIsNone(result[1].value)
        self.assertIs(result[2].quality, Quality.ESTIMATED)
        self.assertIs(result[3].quality, Quality.UNKNOWN)

    def test_sparse_days_sorted_without_padding(self):
        rows = [sample("2025-03-15"), sample("2025-03-10")]
        result = parse_daily_electricity(daily(rows=rows), **CONTEXT)
        self.assertEqual([v.start.day for v in result.snapshot.intervals], [10, 15])

    def test_daylight_saving_days_have_actual_duration(self):
        for day, hours in (("2025-03-30", 23), ("2025-10-26", 25)):
            result = parse_daily_electricity(daily(day), **CONTEXT)
            self.assertEqual(
                result.snapshot.intervals[0].duration, timedelta(hours=hours)
            )

    def test_empty_series_stays_empty(self):
        data = daily()
        data["consumptionsList"]["years"] = []
        data["lastUpdate"] = None
        result = parse_daily_electricity(data, **CONTEXT)
        self.assertEqual(result.snapshot.intervals, ())
        self.assertIsNone(result.last_update)

    def test_missing_lists_are_not_empty_series(self):
        for value in (None, {}, "wrong"):
            data = daily()
            data["consumptionsList"]["years"][0]["months"] = value
            with self.subTest(value=value), self.assertRaises(PayloadError):
                parse_daily_electricity(data, **CONTEXT)

    def test_duplicate_periods_at_every_level_rejected(self):
        for level in ("years", "months", "days"):
            data = daily()
            target = data["consumptionsList"]
            if level != "years":
                target = target["years"][0]
            if level == "days":
                target = target["months"][0]
            target[level].append(copy.deepcopy(target[level][0]))
            with self.subTest(level=level), self.assertRaises(PayloadError):
                parse_daily_electricity(data, **CONTEXT)

    def test_invalid_or_mismatched_periods_rejected(self):
        for reference in (
            "2025-02-28",
            "2025-03-32",
            "2025-04-01",
            "2026-03-10",
            "20250310",
            False,
        ):
            data = daily(rows=[sample(reference)])
            with self.subTest(reference=reference), self.assertRaises(PayloadError):
                parse_daily_electricity(data, **CONTEXT)

    def test_invalid_measurements_rejected_without_using_display_strings(self):
        for value in (True, -1, "1,25", float("nan"), float("inf"), {}, []):
            data = daily(rows=[sample("2025-03-10", value)])
            with self.subTest(value=value), self.assertRaises(PayloadError):
                parse_daily_electricity(data, **CONTEXT)

    def test_missing_value_requires_explicit_missing_quality(self):
        row = sample("2025-03-10")
        del row["totalValue"]
        with self.assertRaises(PayloadError):
            parse_daily_electricity(daily(rows=[row]), **CONTEXT)
        row["totalType"] = "NOT_PROVIDED"
        self.assertIsNone(
            parse_daily_electricity(daily(rows=[row]), **CONTEXT)
            .snapshot.intervals[0]
            .value
        )

    def test_last_update_is_strict_and_not_fetch_time(self):
        data = daily()
        for value in ("", "yesterday", "2025-02-30", True):
            data["lastUpdate"] = value
            with self.assertRaises(PayloadError):
                parse_daily_electricity(data, **CONTEXT)
        del data["lastUpdate"]
        with self.assertRaises(PayloadError):
            parse_daily_electricity(data, **CONTEXT)

    def test_hourly_values_are_separate_from_provider_day_total(self):
        result = parse_hourly_electricity(hourly(), **CONTEXT)
        self.assertIs(result.granularity, Granularity.HOUR)
        self.assertEqual(len(result.snapshot.intervals), 24)
        self.assertTrue(
            all(i.duration == timedelta(hours=1) for i in result.snapshot.intervals)
        )
        self.assertEqual(result.day_total.value, Decimal("8.57"))
        self.assertEqual(result.snapshot.intervals[-1].end.day, 11)

    def test_sparse_hourly_data_is_not_filled(self):
        result = parse_hourly_electricity(hourly(rows=[sample("05:00")]), **CONTEXT)
        self.assertEqual(len(result.snapshot.intervals), 1)

    def test_ambiguous_autumn_hour_rejected_without_guessing_offset(self):
        with self.assertRaisesRegex(PayloadError, "Ambiguous"):
            parse_hourly_electricity(hourly("2025-10-26"), **CONTEXT)

    def test_nonexistent_spring_hour_rejected_but_23_hour_day_valid(self):
        with self.assertRaisesRegex(PayloadError, "nonexistent"):
            parse_hourly_electricity(hourly("2025-03-30"), **CONTEXT)
        rows = [sample(f"{h:02}:00") for h in range(24) if h != 2]
        result = parse_hourly_electricity(hourly("2025-03-30", rows), **CONTEXT)
        self.assertEqual(len(result.snapshot.intervals), 23)
        self.assertEqual(result.snapshot.intervals[1].end.hour, 3)

    def test_invalid_hour_and_duplicate_hour_rejected(self):
        for rows in (
            [sample("00:00"), sample("00:00")],
            [sample("24:00")],
            [sample("01:30")],
            [sample("1:00")],
            [sample(None)],
        ):
            with self.subTest(rows=rows), self.assertRaises(PayloadError):
                parse_hourly_electricity(hourly(rows=rows), **CONTEXT)

    def test_diagnostics_exclude_identifiers_dates_and_quantities(self):
        readings = parse_daily_electricity(daily(), **CONTEXT)
        summary = diagnostic_summary([readings.snapshot])
        serialized = json.dumps(summary)
        for private in ("synthetic-sensitive-id", "2025-03-10", "1.25", "7.31"):
            self.assertNotIn(private, serialized)
        self.assertEqual(summary["supplies"][0]["interval_count"], 1)

    def test_application_errors_on_http_success_are_not_empty_data(self):
        with self.assertRaises(ServiceError) as raised:
            successful_payload(
                {
                    "code": "KO",
                    "description": "synthetic-private",
                    "errorCode": 42,
                    "detailedErrorCode": 42.1,
                }
            )
        self.assertEqual(raised.exception.detailed_code, Decimal("42.1"))
        self.assertNotIn("synthetic-private", str(raised.exception))
        for value in (False, "0", 42):
            with self.assertRaises(ServiceError):
                successful_payload({"code": "OK", "errorCode": value})
        for payload in ({}, {"code": "new"}, {"code": []}):
            with self.assertRaises(PayloadError):
                successful_payload(payload)


class GasTests(unittest.TestCase):
    def parse(self, payload=None, last_update=date(2025, 3, 20)):
        return parse_monthly_gas(
            monthly_gas() if payload is None else payload,
            **CONTEXT,
            last_update=last_update,
        )

    def test_monthly_values_totals_units_quality_and_update_date(self):
        result = self.parse()
        month = result.snapshot.intervals[0]
        self.assertEqual(month.value, Decimal(7))
        self.assertIs(month.unit, Unit.STANDARD_CUBIC_METERS)
        self.assertIs(month.quality, Quality.ACTUAL)
        self.assertEqual(month.start.isoformat(), "2025-03-01T00:00:00+01:00")
        self.assertEqual(month.end.isoformat(), "2025-04-01T00:00:00+02:00")
        self.assertEqual(result.month_totals, result.snapshot.intervals)
        self.assertEqual(result.year_totals[0].value, Decimal(21))
        self.assertEqual(result.last_update, date(2025, 3, 20))
        self.assertEqual(parse_gas_last_update(gas_update()), date(2025, 3, 20))

    def test_missing_zero_estimated_and_sparse_months_remain_distinct(self):
        rows = [
            sample("2025-01", 0),
            sample("2025-03", 0, "NOT_PROVIDED"),
            sample("2025-06", 2.5, "estimated"),
        ]
        result = self.parse(monthly_gas(rows=rows)).snapshot.intervals
        self.assertEqual([item.start.month for item in result], [1, 3, 6])
        self.assertEqual(result[0].value, Decimal(0))
        self.assertIsNone(result[1].value)
        self.assertIs(result[2].quality, Quality.ESTIMATED)

    def test_empty_series_and_missing_update_are_not_fabricated(self):
        data = monthly_gas()
        data["consumptionsList"]["years"] = []
        result = self.parse(data, last_update=None)
        self.assertEqual(result.snapshot.intervals, ())
        self.assertIsNone(result.last_update)
        self.assertIsNone(parse_gas_last_update({"code": "OK", "lastUpdateDate": None}))

    def test_dates_periods_and_duplicates_are_strict(self):
        for value in ("", "2025-02-30", True, 1):
            with self.subTest(value=value), self.assertRaises(PayloadError):
                parse_gas_last_update({"code": "OK", "lastUpdateDate": value})
        data = monthly_gas()
        data["lastUpdate"] = "2025-03-19"
        with self.assertRaisesRegex(PayloadError, "do not match"):
            self.parse(data)
        for reference in ("2025-00", "2025-13", "2026-03", "202503", False):
            data = monthly_gas(rows=[sample(reference)])
            with self.subTest(reference=reference), self.assertRaises(PayloadError):
                self.parse(data)
        data = monthly_gas()
        data["consumptionsList"]["years"][0]["months"] *= 2
        with self.assertRaises(PayloadError):
            self.parse(data)


if __name__ == "__main__":
    unittest.main()

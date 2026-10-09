"""Long-term statistics tests with exclusively invented consumption data."""

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from mobile_fixtures import daily, sample  # noqa: E402

from custom_components.engie_italia.api.mobile import (  # noqa: E402
    ROME,
    parse_daily_electricity,
)
from custom_components.engie_italia.statistics import (  # noqa: E402
    async_import_electricity_statistics,
)

MODULE = "custom_components.engie_italia.statistics."


class ElectricityStatisticsTests(unittest.IsolatedAsyncioTestCase):
    async def test_backfill_preserves_older_points_and_applies_corrections(self):
        readings = parse_daily_electricity(
            daily(
                rows=[
                    sample("2025-03-10", 1.25),
                    sample("2025-03-11", 2),
                ]
            ),
            supply_id="synthetic-power",
            fetched_at=datetime.now(UTC),
        )
        hass = MagicMock()
        hass.config.components = {"recorder"}
        march_10 = datetime(2025, 3, 10, tzinfo=ROME).astimezone(UTC).timestamp()
        march_12 = datetime(2025, 3, 12, tzinfo=ROME).astimezone(UTC).timestamp()
        existing = [
            {
                "start": datetime(2025, 2, 28, tzinfo=UTC).timestamp(),
                "state": 4.0,
                "sum": 10.0,
            },
            {"start": march_10, "state": 1.0, "sum": 11.0},
            {"start": march_12, "state": 3.0, "sum": 14.0},
        ]
        recorder = MagicMock()
        recorder.async_add_executor_job = AsyncMock(return_value=existing)

        with (
            patch(MODULE + "get_instance", return_value=recorder),
            patch(MODULE + "async_add_external_statistics") as add,
        ):
            imported = await async_import_electricity_statistics(
                hass, "a" * 64, readings
            )

        self.assertEqual(imported, 3)
        metadata, statistics = add.call_args.args[1:]
        self.assertEqual(
            metadata["statistic_id"],
            "engie_italia:" + "a" * 64 + "_electricity_consumption",
        )
        self.assertEqual(metadata["unit_of_measurement"], "kWh")
        self.assertEqual(
            [row["state"] for row in statistics],
            [1.25, 2.0, 3.0],
        )
        self.assertEqual(
            [row["sum"] for row in statistics],
            [11.25, 13.25, 16.25],
        )

    async def test_recorder_or_values_may_be_absent(self):
        readings = parse_daily_electricity(
            daily(rows=[]),
            supply_id="synthetic-power",
            fetched_at=datetime.now(UTC),
        )
        hass = MagicMock()
        hass.config.components = set()
        with patch(MODULE + "async_add_external_statistics") as add:
            self.assertEqual(
                await async_import_electricity_statistics(hass, "a" * 64, readings),
                0,
            )
        add.assert_not_called()


if __name__ == "__main__":
    unittest.main()

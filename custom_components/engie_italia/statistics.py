"""Import delayed ENGIE electricity readings as long-term statistics."""

from datetime import UTC, datetime

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    statistics_during_period,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import EnergyConverter

from .api.mobile import ElectricityReadings
from .const import DOMAIN


def electricity_statistic_id(supply_key: str) -> str:
    """Return the stable, non-identifying statistic ID for a supply."""
    return f"{DOMAIN}:{supply_key}_electricity_consumption"


async def async_import_electricity_statistics(
    hass,
    supply_key: str,
    readings: ElectricityReadings,
) -> int:
    """Insert or correct the daily history already returned by ENGIE."""
    if "recorder" not in hass.config.components:
        return 0
    intervals = tuple(
        interval
        for interval in readings.snapshot.intervals
        if interval.value is not None
    )
    if not intervals:
        return 0

    statistic_id = electricity_statistic_id(supply_key)

    def existing_statistics():
        return statistics_during_period(
            hass,
            dt_util.utc_from_timestamp(0),
            None,
            {statistic_id},
            "hour",
            None,
            {"state", "sum"},
        ).get(statistic_id, [])

    existing = await get_instance(hass).async_add_executor_job(existing_statistics)
    first_start = min(interval.start.astimezone(UTC) for interval in intervals)
    first_timestamp = first_start.timestamp()
    baseline = 0.0
    values: dict[float, float] = {}
    for item in existing:
        timestamp = float(item["start"])
        if timestamp < first_timestamp:
            if item.get("sum") is not None:
                baseline = float(item["sum"])
        elif item.get("state") is not None:
            values[timestamp] = float(item["state"])

    # Fresh provider values replace equal timestamps. Existing points omitted by
    # a later partial response are retained instead of being turned into zero.
    values.update(
        {
            interval.start.astimezone(UTC).timestamp(): float(interval.value)
            for interval in intervals
        }
    )
    total = baseline
    statistics = []
    for timestamp, value in sorted(values.items()):
        total += value
        statistics.append(
            StatisticData(
                start=datetime.fromtimestamp(timestamp, UTC),
                state=value,
                sum=total,
            )
        )

    async_add_external_statistics(
        hass,
        StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name="ENGIE Luce - Consumo giornaliero",
            source=DOMAIN,
            statistic_id=statistic_id,
            unit_class=EnergyConverter.UNIT_CLASS,
            unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        ),
        statistics,
    )
    return len(statistics)

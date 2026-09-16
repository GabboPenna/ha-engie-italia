"""Dated consumption summaries, deliberately not cumulative Energy counters."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory, UnitOfEnergy
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api.models import Utility
from .const import DOMAIN

COMMON = (
    SensorEntityDescription(
        key="supply_status",
        translation_key="supply_status",
        device_class=SensorDeviceClass.ENUM,
        options=["active", "unknown"],
    ),
    SensorEntityDescription(
        key="data_status",
        translation_key="data_status",
        device_class=SensorDeviceClass.ENUM,
        options=["available", "no_data", "unsupported", "error"],
    ),
)
ELECTRICITY = (
    SensorEntityDescription(
        key="last_day",
        translation_key="last_day",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    SensorEntityDescription(
        key="last_day_date",
        translation_key="last_day_date",
        device_class=SensorDeviceClass.DATE,
    ),
    SensorEntityDescription(
        key="month",
        translation_key="month",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    SensorEntityDescription(
        key="year",
        translation_key="year",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    SensorEntityDescription(
        key="last_data_update",
        translation_key="last_data_update",
        device_class=SensorDeviceClass.DATE,
    ),
    SensorEntityDescription(
        key="last_sync",
        translation_key="last_sync",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    seen = set()

    @callback
    def add_new():
        entities = []
        for key, data in (coordinator.data or {}).items():
            if key in seen:
                continue
            seen.add(key)
            descriptions = COMMON + (
                ELECTRICITY if data.supply.utility is Utility.ELECTRICITY else ()
            )
            entities.extend(
                EngieSensor(coordinator, entry, key, data.supply.utility, description)
                for description in descriptions
            )
        if entities:
            async_add_entities(entities)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class EngieSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, utility, description):
        super().__init__(coordinator)
        self._key = key
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{key}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.unique_id}_{key}")},
            name="ENGIE Luce" if utility is Utility.ELECTRICITY else "ENGIE Gas",
            manufacturer="ENGIE",
            model="Electricity supply"
            if utility is Utility.ELECTRICITY
            else "Gas supply",
            via_device=(DOMAIN, entry.unique_id),
        )

    @property
    def supply_data(self):
        return (self.coordinator.data or {}).get(self._key)

    @property
    def available(self):
        data = self.supply_data
        if not super().available or data is None:
            return False
        if self.entity_description.key in ("supply_status", "data_status"):
            return True
        return data.status != "error" and data.readings is not None

    def _period(self):
        data = self.supply_data
        if data is None or data.readings is None:
            return None
        readings = data.readings
        key = self.entity_description.key
        periods = (
            readings.month_totals
            if key == "month"
            else readings.year_totals
            if key == "year"
            else readings.snapshot.intervals
        )
        return next(
            (period for period in reversed(periods) if period.value is not None), None
        )

    @property
    def native_value(self):
        data = self.supply_data
        if data is None:
            return None
        key = self.entity_description.key
        if key == "supply_status":
            return data.supply.status.value
        if key == "data_status":
            return data.status
        if data.readings is None:
            return None
        if key == "last_data_update":
            return data.readings.last_update
        if key == "last_sync":
            return data.readings.snapshot.fetched_at
        period = self._period()
        if period is None:
            return None
        return period.start.date() if key == "last_day_date" else period.value

    @property
    def extra_state_attributes(self):
        if self.entity_description.key not in ("last_day", "month", "year"):
            return None
        period = self._period()
        if period is None:
            return None
        return {
            "period_start": period.start.isoformat(),
            "period_end": period.end.isoformat(),
            "quality": period.quality.value,
            "data_date": self.supply_data.readings.last_update.isoformat()
            if self.supply_data.readings.last_update
            else None,
        }

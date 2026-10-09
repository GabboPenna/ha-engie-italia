"""Dated consumption and invoice summaries, without cumulative billing counters."""

from datetime import datetime, time, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfEnergy, UnitOfPower
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api.mobile import ROME
from .api.models import Utility
from .api.tariffs import VERIFIED_TARIFFS, current_tariff, tariff_status
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
        state_class=SensorStateClass.TOTAL,
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
GAS = (
    SensorEntityDescription(
        key="month",
        translation_key="month",
        native_unit_of_measurement="Smc",
    ),
    SensorEntityDescription(
        key="year",
        translation_key="year",
        native_unit_of_measurement="Smc",
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

INVOICES = (
    SensorEntityDescription(
        key="invoice_data_status",
        translation_key="invoice_data_status",
        device_class=SensorDeviceClass.ENUM,
        options=["available", "no_invoices", "incomplete", "error"],
    ),
    SensorEntityDescription(
        key="invoices_count",
        translation_key="invoices_count",
        icon="mdi:file-document-multiple-outline",
    ),
    SensorEntityDescription(
        key="open_invoices",
        translation_key="open_invoices",
        icon="mdi:invoice-text-clock-outline",
    ),
    SensorEntityDescription(
        key="outstanding_amount",
        translation_key="outstanding_amount",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="overdue_invoices",
        translation_key="overdue_invoices",
        icon="mdi:invoice-text-remove-outline",
    ),
    SensorEntityDescription(
        key="latest_invoice",
        translation_key="latest_invoice",
        icon="mdi:invoice-text-outline",
    ),
    SensorEntityDescription(
        key="latest_invoice_amount",
        translation_key="latest_invoice_amount",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="latest_invoice_date",
        translation_key="latest_invoice_date",
        device_class=SensorDeviceClass.DATE,
    ),
    SensorEntityDescription(
        key="latest_invoice_due_date",
        translation_key="latest_invoice_due_date",
        device_class=SensorDeviceClass.DATE,
    ),
    SensorEntityDescription(
        key="earliest_invoice_due_date",
        translation_key="earliest_invoice_due_date",
        device_class=SensorDeviceClass.DATE,
    ),
    SensorEntityDescription(
        key="invoices_last_sync",
        translation_key="invoices_last_sync",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

ACCOUNT = (
    SensorEntityDescription(
        key="next_bill_date",
        translation_key="next_bill_date",
        device_class=SensorDeviceClass.DATE,
    ),
    SensorEntityDescription(
        key="direct_debit",
        translation_key="direct_debit",
        device_class=SensorDeviceClass.ENUM,
        options=["active", "inactive", "mixed", "unknown"],
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="digital_bill",
        translation_key="digital_bill",
        device_class=SensorDeviceClass.ENUM,
        options=["active", "inactive", "mixed", "unknown"],
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

SUPPLY_DETAILS = (
    SensorEntityDescription(
        key="economic_terms_end",
        translation_key="economic_terms_end",
        device_class=SensorDeviceClass.DATE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

ELECTRICITY_DETAILS = (
    SensorEntityDescription(
        key="contracted_power",
        translation_key="contracted_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="available_power",
        translation_key="available_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

GAS_DETAILS = (
    SensorEntityDescription(
        key="self_reading_deadline",
        translation_key="self_reading_deadline",
        device_class=SensorDeviceClass.DATE,
    ),
)

TARIFFS = (
    SensorEntityDescription(
        key="energy_unit_price",
        translation_key="energy_unit_price",
        icon="mdi:currency-eur",
        suggested_display_precision=5,
    ),
    SensorEntityDescription(
        key="annual_fixed_fee",
        translation_key="annual_fixed_fee",
        icon="mdi:calendar-currency",
        native_unit_of_measurement="EUR/year",
        suggested_display_precision=2,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    seen = set()
    account_added = False

    @callback
    def add_new():
        nonlocal account_added
        entities = []
        if not account_added:
            entities.extend(
                EngieAccountSensor(coordinator, entry, description)
                for description in ACCOUNT
            )
            entities.extend(
                EngieInvoiceSensor(coordinator, entry, description)
                for description in INVOICES
            )
            account_added = True
        for key, data in (coordinator.data or {}).items():
            if key in seen:
                continue
            seen.add(key)
            descriptions = COMMON + (
                ELECTRICITY if data.supply.utility is Utility.ELECTRICITY else GAS
            )
            entities.extend(
                EngieSensor(coordinator, entry, key, data.supply.utility, description)
                for description in descriptions
            )
            detail_descriptions = SUPPLY_DETAILS + (
                ELECTRICITY_DETAILS
                if data.supply.utility is Utility.ELECTRICITY
                else GAS_DETAILS
            )
            entities.extend(
                EngieSupplyDetailSensor(
                    coordinator, entry, key, data.supply.utility, description
                )
                for description in detail_descriptions
            )
            entities.extend(
                EngieTariffSensor(
                    coordinator, entry, key, data.supply.utility, description
                )
                for description in TARIFFS
            )
        if entities:
            async_add_entities(entities)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class EngieAccountSensor(CoordinatorEntity, SensorEntity):
    """Account-level contract services independent of invoice availability."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name="ENGIE Italia",
            manufacturer="ENGIE",
            model="Account",
        )

    @property
    def available(self):
        if not super().available:
            return False
        if self.entity_description.key == "next_bill_date":
            return self.coordinator.account.next_bill_date is not None
        return True

    @property
    def native_value(self):
        account = self.coordinator.account
        return {
            "next_bill_date": account.next_bill_date,
            "direct_debit": account.direct_debit.value,
            "digital_bill": account.digital_bill.value,
        }[self.entity_description.key]


class EngieInvoiceSensor(CoordinatorEntity, SensorEntity):
    """Account invoices fetched once per contract, without duplicates per fuel."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name="ENGIE Italia",
            manufacturer="ENGIE",
            model="Account",
        )

    @property
    def available(self):
        if not super().available:
            return False
        if self.entity_description.key in ("invoice_data_status", "invoices_last_sync"):
            return True
        return (
            self.coordinator.billing.status != "error"
            and self.coordinator.billing.snapshot is not None
        )

    @property
    def native_value(self):
        billing = self.coordinator.billing
        key = self.entity_description.key
        if key == "invoice_data_status":
            return billing.status
        snapshot = billing.snapshot
        if snapshot is None:
            return None
        if key == "invoices_last_sync":
            return snapshot.fetched_at
        # Keep the previous snapshot privately on failures without publishing it
        # as a newly retrieved amount (even when queried directly by other code).
        if billing.status == "error":
            return None
        if key == "invoices_count":
            return len(snapshot.invoices)
        if key == "open_invoices":
            return snapshot.open_count
        if key == "outstanding_amount":
            return snapshot.outstanding
        if key == "overdue_invoices":
            return snapshot.overdue_count(dt_util.now().date())
        if key == "earliest_invoice_due_date":
            return snapshot.earliest_due
        latest = snapshot.latest
        if latest is None:
            return None
        return {
            "latest_invoice": latest.reference,
            "latest_invoice_amount": latest.amount,
            "latest_invoice_date": latest.issued,
            "latest_invoice_due_date": latest.due,
        }.get(key)

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != "invoice_data_status":
            return None
        billing = self.coordinator.billing
        return {
            "error_code": billing.error_code,
            "detailed_error_code": billing.detailed_error_code,
        }


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
        if data.status == "error" or data.readings is None:
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
    def last_reset(self):
        if self.entity_description.key != "last_day":
            return None
        data = self.supply_data
        if data is None or data.status == "error":
            return None
        period = self._period()
        return period.start if period is not None else None

    @property
    def extra_state_attributes(self):
        if self.entity_description.key not in ("last_day", "month", "year"):
            return None
        if self.supply_data is None or self.supply_data.status == "error":
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


class EngieSupplyDetailSensor(EngieSensor):
    """Contract metadata that remains useful without consumption readings."""

    def _value(self):
        data = self.supply_data
        if data is None:
            return None
        supply = data.supply
        return {
            "economic_terms_end": supply.offer.valid_until if supply.offer else None,
            "contracted_power": supply.contracted_power,
            "available_power": supply.available_power,
            "self_reading_deadline": supply.self_reading_window_end,
        }[self.entity_description.key]

    @property
    def available(self):
        return self.coordinator.last_update_success and self._value() is not None

    @property
    def native_value(self):
        return self._value()

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != "self_reading_deadline":
            return None
        data = self.supply_data
        if data is None or data.supply.self_reading_window_start is None:
            return None
        return {"window_start": data.supply.self_reading_window_start.isoformat()}


class EngieTariffSensor(EngieSensor):
    """Reviewed energy component, independent of consumption availability."""

    def __init__(self, coordinator, entry, key, utility, description):
        super().__init__(coordinator, entry, key, utility, description)
        self._unsub_midnight = None
        if description.key == "energy_unit_price":
            self._attr_native_unit_of_measurement = (
                "EUR/kWh" if utility is Utility.ELECTRICITY else "EUR/Smc"
            )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._schedule_midnight()

    async def async_will_remove_from_hass(self):
        if self._unsub_midnight is not None:
            self._unsub_midnight()
            self._unsub_midnight = None
        await super().async_will_remove_from_hass()

    @callback
    def _schedule_midnight(self):
        tomorrow = dt_util.now(ROME).date() + timedelta(days=1)
        self._unsub_midnight = async_track_point_in_utc_time(
            self.hass,
            self._async_midnight,
            datetime.combine(tomorrow, time.min, ROME),
        )

    @callback
    def _async_midnight(self, _now):
        # Expire at Italian midnight even if the next API poll is hours away.
        self.async_write_ha_state()
        self._schedule_midnight()

    def _tariff(self):
        if not self.coordinator.last_update_success or self.supply_data is None:
            return None
        return current_tariff(self.supply_data.supply, dt_util.now(ROME).date())

    @property
    def available(self):
        return self._tariff() is not None

    @property
    def native_value(self):
        tariff = self._tariff()
        if tariff is None:
            return None
        return (
            tariff.unit_price
            if self.entity_description.key == "energy_unit_price"
            else tariff.annual_fee
        )

    @property
    def extra_state_attributes(self):
        data = self.supply_data
        if data is None:
            return None
        attrs = {
            "tariff_status": tariff_status(data.supply, dt_util.now(ROME).date())
            if self.coordinator.last_update_success
            else "update_failed",
            "taxes_included": False,
            "all_inclusive": False,
        }
        offer = data.supply.offer
        if offer is not None:
            attrs.update(
                offer_code=offer.code,
                valid_from=offer.valid_from.isoformat(),
                valid_until=offer.valid_until.isoformat(),
            )
            verified = VERIFIED_TARIFFS.get(offer.code)
            if verified is not None:
                attrs["source_url"] = verified.source_url
        tariff = self._tariff()
        if tariff is not None and self.entity_description.key == "energy_unit_price":
            attrs["fixed_fee_included"] = False
            if data.supply.utility is Utility.ELECTRICITY:
                attrs["network_losses_included"] = tariff.network_losses_included
            elif tariff.reference_pcs_gj_smc is not None:
                attrs["reference_pcs_gj_smc"] = str(tariff.reference_pcs_gj_smc)
        return attrs

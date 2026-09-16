"""One polling coordinator per account, isolating failures between supplies."""

import hashlib
import logging
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api.client import EngieMobileClient
from .api.errors import (
    AuthenticationError,
    EngieError,
    ServiceError,
    TokenPersistenceError,
)
from .api.invoices import InvoiceSnapshot
from .api.mobile import ElectricityReadings, MobileSupply
from .api.models import Utility
from .api.portal import SupplyStatus
from .const import CONF_INTERVAL, DEFAULT_INTERVAL_HOURS, DOMAIN

_LOGGER = logging.getLogger(__name__)


def supply_key(supply: MobileSupply) -> str:
    return hashlib.sha256(
        f"{supply.utility.value}:{supply.point_id}".encode()
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class SupplyData:
    supply: MobileSupply
    readings: ElectricityReadings | None = None
    status: str = "no_data"


@dataclass(frozen=True, slots=True)
class BillingData:
    snapshot: InvoiceSnapshot | None = None
    status: str = "error"
    error_code: int | None = None
    detailed_error_code: str | None = None


class EngieCoordinator(DataUpdateCoordinator[dict[str, SupplyData]]):
    def __init__(self, hass, entry: ConfigEntry, client: EngieMobileClient):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(
                hours=entry.options.get(CONF_INTERVAL, DEFAULT_INTERVAL_HOURS)
            ),
        )
        self.client = client
        self._commissioning = {}
        self._commissioning_checked = {}
        self.last_success: datetime | None = None
        self.billing = BillingData()

    async def _async_update_billing(self, today):
        try:
            snapshot = await self.client.async_invoices()
            self.billing = BillingData(snapshot, snapshot.data_status(today))
        except (AuthenticationError, TokenPersistenceError):
            raise
        except (EngieError, ValueError) as error:
            # A billing outage must not hide consumption or expose a partial sum.
            self.billing = BillingData(
                snapshot=self.billing.snapshot,
                status="error",
                error_code=error.error_code
                if isinstance(error, ServiceError)
                else None,
                detailed_error_code=str(error.detailed_code)
                if isinstance(error, ServiceError) and error.detailed_code is not None
                else None,
            )

    async def _async_update_data(self):
        try:
            supplies = await self.client.async_supplies()
            today = dt_util.now().date()
            cache_keys = {
                (s.point_id, s.contract_id, s.activation_date) for s in supplies
            }
            for cache in (self._commissioning, self._commissioning_checked):
                for old in cache.keys() - cache_keys:
                    del cache[old]
            result = {}
            for supply in supplies:
                key = supply_key(supply)
                if key in result:
                    raise UpdateFailed("ENGIE returned duplicate supply points")
                if supply.utility is Utility.GAS:
                    result[key] = SupplyData(supply, status="unsupported")
                    continue
                if supply.status is not SupplyStatus.ACTIVE:
                    result[key] = SupplyData(supply)
                    continue
                try:
                    cache_key = (
                        supply.point_id,
                        supply.contract_id,
                        supply.activation_date,
                    )
                    if self._commissioning_checked.get(cache_key) != today:
                        self._commissioning[
                            cache_key
                        ] = await self.client.async_commissioning_date(supply)
                        self._commissioning_checked[cache_key] = today
                    lower = self.client.lower_bound(
                        supply, self._commissioning[cache_key], today=today
                    )
                    readings = await self.client.async_daily_electricity(
                        supply, lower_bound=lower, year=today.year
                    )
                    if (
                        not any(
                            i.value is not None for i in readings.snapshot.intervals
                        )
                        and lower.year < today.year
                    ):
                        previous = await self.client.async_daily_electricity(
                            supply, lower_bound=lower, year=today.year - 1
                        )
                        if any(
                            i.value is not None for i in previous.snapshot.intervals
                        ):
                            readings = previous
                    status = (
                        "available"
                        if any(i.value is not None for i in readings.snapshot.intervals)
                        else "no_data"
                    )
                    result[key] = SupplyData(supply, readings, status)
                except (AuthenticationError, TokenPersistenceError):
                    raise
                except (EngieError, ValueError):
                    previous = (self.data or {}).get(key)
                    result[key] = (
                        replace(previous, supply=supply, status="error")
                        if previous
                        else SupplyData(supply, status="error")
                    )
            await self._async_update_billing(today)
            self.last_success = dt_util.utcnow()
            return result
        except AuthenticationError as error:
            raise ConfigEntryAuthFailed("ENGIE authorization needs renewal") from error
        except TokenPersistenceError as error:
            raise UpdateFailed("Cannot save the renewed ENGIE session") from error
        except EngieError as error:
            raise UpdateFailed("ENGIE account update unavailable") from error

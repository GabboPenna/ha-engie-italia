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
from .api.errors import AuthenticationError, EngieError, TokenPersistenceError
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

    async def _async_update_data(self):
        try:
            supplies = await self.client.async_supplies()
            today = dt_util.now().date()
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
                    if self._commissioning_checked.get(supply.point_id) != today:
                        self._commissioning[
                            supply.point_id
                        ] = await self.client.async_commissioning_date(supply)
                        self._commissioning_checked[supply.point_id] = today
                    lower = self.client.lower_bound(
                        supply, self._commissioning[supply.point_id], today=today
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
            self.last_success = dt_util.utcnow()
            return result
        except AuthenticationError as error:
            raise ConfigEntryAuthFailed("ENGIE authorization needs renewal") from error
        except TokenPersistenceError as error:
            raise UpdateFailed("Cannot save the renewed ENGIE session") from error
        except EngieError as error:
            raise UpdateFailed("ENGIE account update unavailable") from error

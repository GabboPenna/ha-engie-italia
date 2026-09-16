"""Bounded, read-only mobile API client; credentials are supplied out of band."""

import asyncio
import json
import math
import time
from datetime import UTC, date, datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime

import aiohttp

from .errors import AuthenticationError, PayloadError, RateLimitError, TransportError
from .mobile import (
    ROME,
    ElectricityReadings,
    MobileSupply,
    iso_date,
    parse_daily_electricity,
    parse_hourly_electricity,
    parse_mobile_supplies,
    service_error,
    successful_payload,
)
from .models import Utility

API = "https://api-mobileapp2022-prod.aws.engie.it/"
TOKEN_URL = "https://login.engie.it/oauth/token"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
READ_PATHS = frozenset(
    {
        "contracts/v2/user",
        "consumptions/v2/power/getCommissioningDate",
        "consumptions/v3/power/daily",
        "consumptions/v3/power/hourly",
    }
)


def _secret(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or any(ord(c) < 33 or ord(c) == 127 for c in value)
    ):
        raise ValueError("Invalid credential configuration")
    return value


def _retry_seconds(value: str | None) -> float:
    try:
        if value is not None and value.isascii() and value.isdigit():
            return max(1, int(value))
        if value:
            when = parsedate_to_datetime(value)
            if when.utcoffset() is not None:
                return max(1, (when - datetime.now(UTC)).total_seconds())
    except (ValueError, TypeError, OverflowError):
        pass
    return 60


class EngieMobileClient:
    """Reuse a caller-owned session, with no logging or credential persistence.

    Initial OAuth/PKCE login and secure refresh-token persistence belong to the
    future config flow. This research client only refreshes its in-memory session.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        api_key: str,
        access_token: str,
        client_id: str | None = None,
        refresh_token: str | None = None,
        expires_in: int | None = None,
    ) -> None:
        self._session = session
        self._api_key = _secret(api_key)
        self._access_token = _secret(access_token)
        self._client_id = _secret(client_id) if client_id is not None else None
        self._refresh_token = (
            _secret(refresh_token) if refresh_token is not None else None
        )
        if (client_id is None) != (refresh_token is None):
            raise ValueError(
                "Refresh token and OAuth client ID must be supplied together"
            )
        if expires_in is not None and (type(expires_in) is not int or expires_in <= 0):
            raise ValueError("Invalid token lifetime")
        self._expires_at = (
            time.monotonic() + expires_in if expires_in is not None else math.inf
        )
        self._lock = asyncio.Lock()
        self._retry_at = 0.0
        self._auth_failed = False

    def clear_credentials(self) -> None:
        """Forget in-memory credentials; close the caller's session separately."""
        self._access_token = ""
        self._refresh_token = None
        self._api_key = ""
        self._client_id = None
        self._auth_failed = True

    def _ready(self) -> None:
        if self._auth_failed:
            raise AuthenticationError("Interactive login required")
        remaining = self._retry_at - time.monotonic()
        if remaining > 0:
            raise RateLimitError(remaining)

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        self._ready()
        try:
            async with self._session.request(
                method,
                url,
                timeout=aiohttp.ClientTimeout(total=20),
                allow_redirects=False,
                raise_for_status=False,
                **kwargs,
            ) as response:
                if response.status == 429:
                    delay = _retry_seconds(response.headers.get("Retry-After"))
                    self._retry_at = time.monotonic() + delay
                    raise RateLimitError(delay)
                if response.status == 401:
                    raise AuthenticationError("Access token rejected")
                if url == TOKEN_URL and response.status in (400, 403):
                    self._auth_failed = True
                    raise AuthenticationError("Interactive login required")
                if 300 <= response.status < 400:
                    raise service_error(response.status, None)
                chunks, size = [], 0
                async for chunk in response.content.iter_chunked(65536):
                    size += len(chunk)
                    if size > MAX_RESPONSE_BYTES:
                        raise PayloadError("Response exceeds size limit")
                    chunks.append(chunk)
                try:
                    payload = json.loads(b"".join(chunks), parse_float=Decimal)
                except (ValueError, UnicodeError):
                    if response.status != 200:
                        raise service_error(response.status, None) from None
                    raise PayloadError("Response is not valid JSON") from None
                if response.status != 200:
                    raise service_error(response.status, payload)
                if not isinstance(payload, dict):
                    raise PayloadError("Expected a response object")
                return payload
        except (aiohttp.ClientError, TimeoutError):
            raise TransportError("ENGIE transport failed") from None

    async def _refresh(self) -> None:
        if not self._refresh_token or not self._client_id:
            self._auth_failed = True
            raise AuthenticationError("Interactive login required")
        try:
            payload = await self._request(
                "POST",
                TOKEN_URL,
                json={
                    "grant_type": "refresh_token",
                    "client_id": self._client_id,
                    "refresh_token": self._refresh_token,
                },
            )
        except AuthenticationError:
            self._auth_failed = True
            raise
        except PayloadError:
            self._auth_failed = True
            raise AuthenticationError(
                "Invalid token response; login required"
            ) from None
        try:
            token = _secret(payload.get("access_token"))
            refresh = _secret(payload.get("refresh_token", self._refresh_token))
            lifetime = payload.get("expires_in")
            if (
                payload.get("token_type", "").lower() != "bearer"
                or type(lifetime) is not int
                or lifetime <= 0
            ):
                raise ValueError("Invalid token response")
        except (ValueError, AttributeError):
            # A rotating refresh token might already have been consumed.
            self._auth_failed = True
            raise AuthenticationError(
                "Invalid token response; login required"
            ) from None
        self._access_token, self._refresh_token = token, refresh
        self._expires_at = time.monotonic() + lifetime

    async def async_refresh(self) -> None:
        async with self._lock:
            self._ready()
            await self._refresh()

    async def _get(self, path: str, params: dict | None = None) -> dict:
        if path not in READ_PATHS:
            raise ValueError("Operation is not an approved read")
        async with self._lock:
            self._ready()
            refreshed = False
            if time.monotonic() >= self._expires_at - 30:
                await self._refresh()
                refreshed = True
            for attempt in range(2):
                try:
                    payload = await self._request(
                        "GET",
                        API + path,
                        params=params,
                        headers={
                            "sessionToken": self._access_token,
                            "x-api-key": self._api_key,
                            "locale": "IT",
                            "Accept": "application/json",
                            "User-Agent": "ha-engie-italia/0.0.1 (read-only research)",
                        },
                    )
                    return successful_payload(payload)
                except AuthenticationError:
                    if refreshed or attempt:
                        self._auth_failed = True
                        raise
                    await self._refresh()
                    refreshed = True
        raise AuthenticationError("Interactive login required")

    async def async_supplies(self) -> tuple[MobileSupply, ...]:
        return parse_mobile_supplies(await self._get("contracts/v2/user"))

    @staticmethod
    def _electricity(supply: MobileSupply) -> None:
        if (
            not isinstance(supply, MobileSupply)
            or supply.utility is not Utility.ELECTRICITY
        ):
            raise ValueError("An electricity supply is required")

    async def async_commissioning_date(self, supply: MobileSupply) -> date | None:
        self._electricity(supply)
        data = await self._get(
            "consumptions/v2/power/getCommissioningDate", {"pod": supply.point_id}
        )
        if "commissioningDate" not in data:
            raise PayloadError("Missing commissioning date field")
        value = data["commissioningDate"]
        return iso_date(value) if value is not None else None

    @staticmethod
    def lower_bound(
        supply: MobileSupply, commissioning_date: date | None, *, today: date
    ) -> date:
        """Match the observed app: commissioning/activation, at most two years back."""
        EngieMobileClient._electricity(supply)
        if type(today) is not date or (
            commissioning_date is not None and type(commissioning_date) is not date
        ):
            raise ValueError("Calendar dates are required")
        source = (
            commissioning_date
            if commissioning_date is not None
            else supply.activation_date
        )
        if source is None:
            raise PayloadError("No verified lower-bound date is available")
        return max(source, date(today.year - 2, 1, 1))

    async def async_daily_electricity(
        self,
        supply: MobileSupply,
        *,
        lower_bound: date,
        year: int,
    ) -> ElectricityReadings:
        self._electricity(supply)
        if (
            type(lower_bound) is not date
            or type(year) is not int
            or not 1 <= year < 9999
        ):
            raise ValueError("A calendar lower bound and valid year are required")
        if year < lower_bound.year:
            raise ValueError("Requested year precedes the lower bound")
        data = await self._get(
            "consumptions/v3/power/daily",
            {
                "pod": supply.point_id,
                "lowerBoundDate": lower_bound.isoformat(),
                "startYear": str(year),
                "endYear": str(year),
            },
        )
        result = parse_daily_electricity(
            data, supply_id=supply.supply_id, fetched_at=datetime.now(UTC)
        )
        bounds = data["consumptionsList"]
        if bounds["startYear"] != str(year) or bounds["endYear"] != str(year):
            raise PayloadError("Response does not match the requested year")
        return result

    async def async_hourly_electricity(
        self,
        supply: MobileSupply,
        *,
        lower_bound: date,
        day: date,
    ) -> ElectricityReadings:
        self._electricity(supply)
        if type(lower_bound) is not date or type(day) is not date or day < lower_bound:
            raise ValueError("A valid day and calendar lower bound are required")
        data = await self._get(
            "consumptions/v3/power/hourly",
            {
                "pod": supply.point_id,
                "lowerBoundDate": lower_bound.isoformat(),
                "day": day.isoformat(),
            },
        )
        result = parse_hourly_electricity(
            data, supply_id=supply.supply_id, fetched_at=datetime.now(UTC)
        )
        if result.day_total.start.astimezone(ROME).date() != day:
            raise PayloadError("Response does not match the requested day")
        return result

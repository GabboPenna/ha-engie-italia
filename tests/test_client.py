import asyncio
import json
import unittest
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from email.utils import format_datetime
from unittest.mock import patch

import aiohttp
from engie_italia.client import API, TOKEN_URL, EngieMobileClient, _retry_seconds
from engie_italia.errors import (
    AuthenticationError,
    PayloadError,
    RateLimitError,
    ServiceError,
    TokenPersistenceError,
    TransportError,
)
from engie_italia.mobile import parse_mobile_supplies
from mobile_fixtures import daily, hourly, supplies


class Response:
    def __init__(self, status=200, payload=None, *, raw=None, headers=None):
        self.status = status
        self.raw = raw if raw is not None else json.dumps(payload).encode()
        self.headers = headers or {}
        self.content = self

    async def iter_chunked(self, size):
        for index in range(0, len(self.raw), size):
            yield self.raw[index : index + size]


class Session:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    @asynccontextmanager
    async def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        result = self.responses.pop(0)
        await asyncio.sleep(0)
        if isinstance(result, Exception):
            raise result
        yield result


def token(**overrides):
    return Response(
        payload={
            "access_token": "synthetic-new-access",
            "refresh_token": "synthetic-new-refresh",
            "expires_in": 3600,
            "token_type": "Bearer",
            **overrides,
        }
    )


def client(session, **kwargs):
    return EngieMobileClient(
        session,
        api_key="synthetic-api-key",
        access_token="synthetic-access",
        client_id="synthetic-client",
        refresh_token="synthetic-refresh",
        **kwargs,
    )


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_rotated_token_persisted_before_next_read(self):
        saved = []

        async def persist(tokens):
            self.assertEqual(len(session.calls), 1)
            saved.append(tokens)

        session = Session(token(), Response(payload=supplies()))
        reader = client(session, expires_in=1, token_updated=persist)
        await reader.async_supplies()
        self.assertEqual(saved[0].refresh_token, "synthetic-new-refresh")

    async def test_storage_failure_retries_save_without_reusing_old_token(self):
        attempts = []

        async def persist(tokens):
            attempts.append(tokens)
            if len(attempts) == 1:
                raise OSError("synthetic-private-disk-error")

        session = Session(token(), Response(payload=supplies()))
        reader = client(session, expires_in=1, token_updated=persist)
        with self.assertRaises(TokenPersistenceError) as error:
            await reader.async_supplies()
        self.assertNotIn("synthetic", str(error.exception))
        self.assertEqual(len(session.calls), 1)
        await reader.async_supplies()
        self.assertEqual(attempts[0], attempts[1])
        self.assertEqual([call[0] for call in session.calls], ["POST", "GET"])

    async def test_supplies_use_only_verified_read_and_headers(self):
        session = Session(Response(payload=supplies()))
        reader = client(session)
        result = await reader.async_supplies()
        self.assertEqual(len(result), 2)
        method, url, options = session.calls[0]
        self.assertEqual((method, url), ("GET", API + "contracts/v2/user"))
        self.assertFalse(options["allow_redirects"])
        self.assertFalse(options["raise_for_status"])
        self.assertEqual(options["timeout"].total, 20)
        self.assertEqual(options["headers"]["sessionToken"], "synthetic-access")
        self.assertNotIn("Authorization", options["headers"])
        self.assertNotIn("synthetic", repr(reader))

    async def test_daily_and_hourly_parameters_and_results(self):
        session = Session(Response(payload=daily()), Response(payload=hourly()))
        reader = client(session)
        supply = parse_mobile_supplies(supplies())[0]
        lower = date(2025, 3, 1)
        days = await reader.async_daily_electricity(
            supply, lower_bound=lower, year=2025
        )
        hours = await reader.async_hourly_electricity(
            supply, lower_bound=lower, day=date(2025, 3, 10)
        )
        self.assertEqual(len(days.snapshot.intervals), 1)
        self.assertEqual(len(hours.snapshot.intervals), 24)
        self.assertEqual(
            session.calls[0][2]["params"],
            {
                "pod": "synthetic-pod",
                "lowerBoundDate": "2025-03-01",
                "startYear": "2025",
                "endYear": "2025",
            },
        )
        self.assertEqual(session.calls[1][2]["params"]["day"], "2025-03-10")

    async def test_commissioning_date_and_activation_fallback(self):
        session = Session(
            Response(payload={"code": "OK", "commissioningDate": "2025-03-02"}),
            Response(payload={"code": "OK", "commissioningDate": None}),
        )
        reader = client(session)
        supply = parse_mobile_supplies(supplies())[0]
        value = await reader.async_commissioning_date(supply)
        self.assertEqual(value, date(2025, 3, 2))
        self.assertEqual(
            reader.lower_bound(supply, value, today=date(2025, 4, 1)), value
        )
        self.assertIsNone(await reader.async_commissioning_date(supply))
        self.assertEqual(
            reader.lower_bound(supply, None, today=date(2025, 4, 1)),
            supply.activation_date,
        )
        self.assertEqual(
            reader.lower_bound(supply, date(2020, 1, 1), today=date(2025, 4, 1)),
            date(2023, 1, 1),
        )

    async def test_expired_token_refreshed_only_once_for_concurrent_reads(self):
        session = Session(
            Response(401),
            token(),
            Response(payload=supplies()),
            Response(payload=supplies()),
        )
        reader = client(session)
        result = await asyncio.gather(reader.async_supplies(), reader.async_supplies())
        self.assertEqual([len(x) for x in result], [2, 2])
        self.assertEqual([c[0] for c in session.calls], ["GET", "POST", "GET", "GET"])
        refresh = session.calls[1]
        self.assertEqual(refresh[1], TOKEN_URL)
        self.assertEqual(refresh[2]["json"]["grant_type"], "refresh_token")
        self.assertNotIn("headers", refresh[2])
        self.assertEqual(
            session.calls[2][2]["headers"]["sessionToken"], "synthetic-new-access"
        )

    async def test_proactive_refresh_not_followed_by_second_refresh(self):
        session = Session(token(), Response(401))
        reader = client(session, expires_in=1)
        with self.assertRaises(AuthenticationError):
            await reader.async_supplies()
        with self.assertRaises(AuthenticationError):
            await reader.async_supplies()
        self.assertEqual(len(session.calls), 2)

    async def test_repeated_401_requires_login_without_further_requests(self):
        session = Session(Response(401), token(), Response(401))
        reader = client(session)
        for _ in range(3):
            with self.assertRaises(AuthenticationError):
                await reader.async_supplies()
        self.assertEqual(len(session.calls), 3)

    async def test_revoked_refresh_token_requires_login(self):
        for status in (400, 401, 403):
            session = Session(
                Response(401), Response(status, raw=b"private-provider-message")
            )
            reader = client(session)
            for _ in range(2):
                with self.assertRaises(AuthenticationError) as error:
                    await reader.async_supplies()
                self.assertNotIn("private", str(error.exception))
            self.assertEqual(len(session.calls), 2)

    async def test_refresh_rotation_stays_in_memory(self):
        session = Session(token(), token(access_token="synthetic-next-access"))
        reader = client(session)
        await reader.async_refresh()
        await reader.async_refresh()
        self.assertEqual(
            session.calls[1][2]["json"]["refresh_token"], "synthetic-new-refresh"
        )

    async def test_nonrotating_refresh_token_is_retained(self):
        session = Session(
            Response(
                payload={
                    "access_token": "synthetic-new",
                    "token_type": "Bearer",
                    "expires_in": 300,
                }
            ),
            token(),
        )
        reader = client(session)
        await reader.async_refresh()
        await reader.async_refresh()
        self.assertEqual(
            session.calls[1][2]["json"]["refresh_token"], "synthetic-refresh"
        )

    async def test_malformed_refresh_does_not_retry_consumed_token(self):
        for override in (
            {"access_token": ""},
            {"refresh_token": None},
            {"expires_in": True},
            {"expires_in": 0},
            {"token_type": "wrong"},
            {"token_type": None},
        ):
            session = Session(token(**override))
            reader = client(session)
            for _ in range(2):
                with self.assertRaises(AuthenticationError):
                    await reader.async_refresh()
            self.assertEqual(len(session.calls), 1)

    async def test_rate_limit_blocks_more_reads_without_sleeping_or_login(self):
        session = Session(Response(429, headers={"Retry-After": "120"}))
        reader = client(session)
        for _ in range(2):
            with self.assertRaises(RateLimitError) as error:
                await reader.async_supplies()
            self.assertGreater(error.exception.retry_after, 115)
        self.assertEqual(len(session.calls), 1)

    async def test_invalid_refresh_json_is_not_retried_with_old_token(self):
        session = Session(Response(raw=b"invalid JSON"))
        reader = client(session)
        for _ in range(2):
            with self.assertRaises(AuthenticationError):
                await reader.async_refresh()
        self.assertEqual(len(session.calls), 1)

    async def test_403_5xx_and_gas_like_errors_are_not_zero_or_login_loops(self):
        for status in (403, 404, 422, 500, 503):
            session = Session(
                Response(
                    status,
                    {
                        "code": "KO",
                        "errorCode": 42,
                        "detailedErrorCode": 42.1,
                        "description": "synthetic-private-account-data",
                    },
                )
            )
            with self.assertRaises(ServiceError) as error:
                await client(session).async_supplies()
            self.assertEqual(error.exception.status, status)
            self.assertEqual(error.exception.detailed_code, Decimal("42.1"))
            self.assertNotIn("synthetic", str(error.exception))
            self.assertEqual(len(session.calls), 1)

    async def test_application_error_with_http_200_is_preserved(self):
        session = Session(
            Response(payload={"code": "KO", "description": "synthetic-private"})
        )
        with self.assertRaises(ServiceError):
            await client(session).async_supplies()

    async def test_redirects_never_send_tokens_elsewhere(self):
        session = Session(
            Response(302, headers={"Location": "https://example.invalid/collect"})
        )
        with self.assertRaises(ServiceError):
            await client(session).async_supplies()
        self.assertEqual(len(session.calls), 1)
        self.assertFalse(session.calls[0][2]["allow_redirects"])

    async def test_invalid_json_and_oversized_responses_are_rejected(self):
        for raw in (b"<html>synthetic-private</html>", b"\xff"):
            with self.assertRaises(PayloadError) as error:
                await client(Session(Response(raw=raw))).async_supplies()
            self.assertNotIn("synthetic", str(error.exception))
        with (
            patch("engie_italia.client.MAX_RESPONSE_BYTES", 10),
            self.assertRaises(PayloadError),
        ):
            await client(Session(Response(raw=b"x" * 11))).async_supplies()

    async def test_network_errors_are_sanitized_and_not_retried(self):
        for exception in (
            TimeoutError("synthetic-private-url"),
            aiohttp.ClientConnectionError("synthetic-token"),
        ):
            session = Session(exception)
            with self.assertRaises(TransportError) as error:
                await client(session).async_supplies()
            self.assertNotIn("synthetic", str(error.exception))
            self.assertEqual(len(session.calls), 1)

    async def test_only_allowlisted_operations_are_possible(self):
        session = Session()
        reader = client(session)
        for path in ("user/delete", "https://example.invalid/", "../contracts/v2/user"):
            with self.assertRaises(ValueError):
                await reader._get(path)
        self.assertEqual(session.calls, [])

    async def test_clear_credentials_prevents_network_calls(self):
        session = Session()
        reader = client(session)
        reader.clear_credentials()
        with self.assertRaises(AuthenticationError):
            await reader.async_supplies()
        self.assertEqual(session.calls, [])

    async def test_gas_supply_and_invalid_dates_rejected_before_network(self):
        session = Session()
        reader = client(session)
        power, gas = parse_mobile_supplies(supplies())
        with self.assertRaises(ValueError):
            await reader.async_daily_electricity(
                gas, lower_bound=date(2025, 3, 1), year=2025
            )
        for year in (True, "2025", 2024):
            with self.assertRaises(ValueError):
                await reader.async_daily_electricity(
                    power, lower_bound=date(2025, 3, 1), year=year
                )
        with self.assertRaises(ValueError):
            await reader.async_hourly_electricity(
                power, lower_bound=date(2025, 3, 1), day=date(2025, 2, 1)
            )
        self.assertEqual(session.calls, [])

    async def test_response_for_wrong_requested_period_rejected(self):
        reader = client(Session(Response(payload=daily()), Response(payload=hourly())))
        power = parse_mobile_supplies(supplies())[0]
        with self.assertRaises(PayloadError):
            await reader.async_daily_electricity(
                power, lower_bound=date(2025, 3, 1), year=2026
            )
        with self.assertRaises(PayloadError):
            await reader.async_hourly_electricity(
                power, lower_bound=date(2025, 3, 1), day=date(2025, 3, 11)
            )


class ConfigurationTests(unittest.TestCase):
    def test_invalid_credentials_do_not_echo_input(self):
        for value in (None, "", "synthetic\r\nsecret", True):
            with self.assertRaises(ValueError) as error:
                EngieMobileClient(Session(), api_key=value, access_token="synthetic")
            self.assertNotIn("synthetic", str(error.exception))

    def test_retry_after_parses_seconds_dates_and_invalid_headers(self):
        self.assertEqual(_retry_seconds("120"), 120)
        future = datetime.now(UTC) + timedelta(minutes=3)
        self.assertGreater(_retry_seconds(format_datetime(future)), 175)
        for value in (None, "bad", "-5", "NaN"):
            self.assertEqual(_retry_seconds(value), 60)


if __name__ == "__main__":
    unittest.main()

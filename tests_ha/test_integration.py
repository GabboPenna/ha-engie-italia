"""Real HA framework with temporary storage and exclusively invented account data."""

import json
import stat
import struct
import sys
import tempfile
import time
import unittest
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from invoice_fixtures import invoice, invoices  # noqa: E402
from mobile_fixtures import daily, supplies  # noqa: E402

from custom_components.engie_italia.api.client import EngieMobileClient  # noqa: E402
from custom_components.engie_italia.api.errors import (  # noqa: E402
    AuthenticationError,
    AuthorizationError,
    AuthorizationFailure,
    ServiceError,
    TokenPersistenceError,
    TransportError,
)
from custom_components.engie_italia.api.invoices import (  # noqa: E402
    InvoiceSnapshot,
    parse_invoices,
)
from custom_components.engie_italia.api.mobile import (  # noqa: E402
    parse_daily_electricity,
    parse_mobile_supplies,
)
from custom_components.engie_italia.api.session import SessionTokens  # noqa: E402
from custom_components.engie_italia.config_flow import EngieConfigFlow  # noqa: E402
from custom_components.engie_italia.const import DEFAULT_CLIENT_ID  # noqa: E402
from custom_components.engie_italia.coordinator import (  # noqa: E402
    EngieCoordinator,
    supply_key,
)
from custom_components.engie_italia.diagnostics import (  # noqa: E402
    async_get_config_entry_diagnostics,
)
from custom_components.engie_italia.sensor import (  # noqa: E402
    COMMON,
    ELECTRICITY,
    INVOICES,
    EngieInvoiceSensor,
    EngieSensor,
)
from custom_components.engie_italia.sensor import (
    async_setup_entry as setup_sensors,
)
from custom_components.engie_italia.storage import (  # noqa: E402
    STORES,
    async_load_credentials,
    async_remove_credentials,
    async_save_credentials,
    credential_store,
    credentials,
)

ACCOUNT = "a" * 64
MODULE = "custom_components.engie_italia."


class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.hass = HomeAssistant(self.directory.name)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.entry = ConfigEntry(
            domain="engie_italia",
            title="ENGIE Italia",
            data={"account_key": ACCOUNT},
            options={},
            source="user",
            unique_id=ACCOUNT,
            version=1,
            minor_version=1,
            discovery_keys=MappingProxyType({}),
            subentries_data=None,
        )
        self.power, self.gas = parse_mobile_supplies(supplies())
        self.readings = parse_daily_electricity(
            daily(), supply_id="synthetic-power", fetched_at=datetime.now(UTC)
        )
        self.client = MagicMock(spec=EngieMobileClient)
        self.client.async_supplies = AsyncMock(return_value=(self.power, self.gas))
        self.client.async_commissioning_date = AsyncMock(return_value=date(2025, 3, 1))
        self.client.async_daily_electricity = AsyncMock(return_value=self.readings)
        self.client.async_invoices = AsyncMock(
            return_value=InvoiceSnapshot((), datetime(2025, 3, 11, tzinfo=UTC))
        )
        self.client.lower_bound = EngieMobileClient.lower_bound
        self.coordinator = EngieCoordinator(self.hass, self.entry, self.client)
        self.entry.runtime_data = self.coordinator
        self.clock = patch(
            MODULE + "coordinator.dt_util.now",
            return_value=datetime(2025, 3, 11, tzinfo=UTC),
        )
        self.clock.start()
        self.app_profile = patch(
            MODULE + "config_flow.DEFAULT_API_KEY", "synthetic-app-key"
        )
        self.app_profile.start()

    async def asyncTearDown(self):
        self.clock.stop()
        self.app_profile.stop()
        await self.coordinator.async_shutdown()
        await self.hass.async_stop(force=True)
        self.directory.cleanup()

    async def refresh(self):
        self.coordinator.data = await self.coordinator._async_update_data()

    def sensor(self, key):
        description = next(d for d in COMMON + ELECTRICITY if d.key == key)
        return EngieSensor(
            self.coordinator,
            self.entry,
            supply_key(self.power),
            self.power.utility,
            description,
        )

    def invoice_sensor(self, key):
        description = next(d for d in INVOICES if d.key == key)
        return EngieInvoiceSensor(self.coordinator, self.entry, description)

    async def test_account_invoice_sensors_expose_residual_dates_and_stable_reference(
        self,
    ):
        self.client.async_invoices.return_value = InvoiceSnapshot(
            parse_invoices(
                invoices(
                    invoice(),
                    invoice(
                        fiscalNumber="SYNTHETIC-PARTIAL",
                        emissionDate="2025-02-01",
                        invoiceStatus="PARTIALLY_PAID",
                        unpaidRemainingAmount=20.25,
                        expiryDate="2025-03-10",
                    ),
                )
            ),
            datetime(2025, 3, 11, tzinfo=UTC),
        )
        await self.refresh()
        expected = {
            "invoice_data_status": "available",
            "invoices_count": 2,
            "open_invoices": 2,
            "outstanding_amount": Decimal("121.00"),
            "overdue_invoices": 1,
            "latest_invoice": "SYNTHETIC-2025-002",
            "latest_invoice_amount": Decimal("100.75"),
            "latest_invoice_date": date(2025, 3, 1),
            "latest_invoice_due_date": date(2025, 3, 20),
            "earliest_invoice_due_date": date(2025, 3, 10),
            "invoices_last_sync": datetime(2025, 3, 11, tzinfo=UTC),
        }
        for key, value in expected.items():
            sensor = self.invoice_sensor(key)
            self.assertEqual(sensor.native_value, value, key)
            self.assertTrue(sensor.available, key)
            self.assertIsNone(sensor.state_class)
            self.assertEqual(
                sensor.device_info["identifiers"], {("engie_italia", ACCOUNT)}
            )
        self.assertEqual(
            self.invoice_sensor("outstanding_amount").native_unit_of_measurement, "EUR"
        )
        self.client.async_invoices.assert_awaited_once()
        diagnostics = json.dumps(
            await async_get_config_entry_diagnostics(self.hass, self.entry)
        )
        self.assertNotIn("SYNTHETIC", diagnostics)
        self.assertNotIn("121.00", diagnostics)
        self.assertNotIn("100.75", diagnostics)

    async def test_invoice_outage_preserves_consumption_and_never_reports_zero_debt(
        self,
    ):
        await self.refresh()
        last_sync = self.invoice_sensor("invoices_last_sync").native_value
        self.client.async_invoices.side_effect = ServiceError(200, 9, Decimal("9.91"))
        await self.refresh()
        self.assertTrue(self.sensor("last_day").available)
        self.assertEqual(
            self.invoice_sensor("invoice_data_status").native_value, "error"
        )
        self.assertEqual(
            self.invoice_sensor("invoice_data_status").extra_state_attributes,
            {"error_code": 9, "detailed_error_code": "9.91"},
        )
        for description in INVOICES:
            if description.key not in ("invoice_data_status", "invoices_last_sync"):
                sensor = self.invoice_sensor(description.key)
                self.assertFalse(sensor.available, description.key)
                self.assertIsNone(sensor.native_value, description.key)
        self.assertEqual(
            self.invoice_sensor("invoices_last_sync").native_value, last_sync
        )
        self.client.async_invoices.side_effect = None
        await self.refresh()
        self.assertEqual(
            self.invoice_sensor("invoice_data_status").native_value, "no_invoices"
        )
        self.assertEqual(
            self.invoice_sensor("outstanding_amount").native_value, Decimal(0)
        )
        self.assertTrue(self.invoice_sensor("outstanding_amount").available)
        self.assertIsNone(
            self.invoice_sensor("invoice_data_status").extra_state_attributes[
                "error_code"
            ]
        )

    async def test_incomplete_invoice_data_leaves_known_fields_usable(self):
        self.client.async_invoices.return_value = InvoiceSnapshot(
            parse_invoices(
                invoices(
                    invoice(unpaidRemainingAmount=None),
                )
            ),
            datetime.now(UTC),
        )
        await self.refresh()
        self.assertEqual(
            self.invoice_sensor("invoice_data_status").native_value, "incomplete"
        )
        self.assertTrue(self.invoice_sensor("outstanding_amount").available)
        self.assertIsNone(self.invoice_sensor("outstanding_amount").native_value)
        self.assertEqual(self.invoice_sensor("open_invoices").native_value, 1)
        self.assertEqual(
            self.invoice_sensor("latest_invoice").native_value, "SYNTHETIC-2025-002"
        )

    async def test_billing_auth_and_storage_failures_propagate_to_coordinator(self):
        from homeassistant.helpers.update_coordinator import UpdateFailed

        for source, target in (
            (AuthenticationError("expired"), ConfigEntryAuthFailed),
            (TokenPersistenceError("disk"), UpdateFailed),
        ):
            self.client.async_invoices.side_effect = source
            with self.assertRaises(target):
                await self.refresh()

    async def test_gas_is_metadata_only_and_power_totals_are_dated(self):
        await self.refresh()
        self.assertEqual(
            self.coordinator.data[supply_key(self.gas)].status, "unsupported"
        )
        self.client.async_daily_electricity.assert_awaited_once()
        sensor = self.sensor("last_day")
        self.assertEqual(float(sensor.native_value), 1.25)
        self.assertTrue(sensor.available)
        self.assertIsNone(sensor.state_class)
        self.assertEqual(
            sensor.extra_state_attributes["period_start"][:10], "2025-03-10"
        )
        self.assertEqual(float(self.sensor("month").native_value), 7.31)
        self.assertEqual(self.sensor("last_day_date").native_value, date(2025, 3, 10))

    async def test_per_supply_failure_does_not_hide_gas_or_report_old_value_as_live(
        self,
    ):
        await self.refresh()
        self.client.async_daily_electricity.side_effect = TransportError("offline")
        await self.refresh()
        self.assertFalse(self.sensor("last_day").available)
        self.assertEqual(self.sensor("data_status").native_value, "error")
        self.assertEqual(
            self.coordinator.data[supply_key(self.gas)].status, "unsupported"
        )

    async def test_auth_failure_requests_reauthentication(self):
        self.client.async_daily_electricity.side_effect = AuthenticationError("expired")
        with self.assertRaises(ConfigEntryAuthFailed):
            await self.refresh()

    async def test_january_falls_back_to_last_available_year(self):
        empty = parse_daily_electricity(
            daily("2026-01-01", rows=[]),
            supply_id="synthetic-power",
            fetched_at=datetime.now(UTC),
        )
        previous = parse_daily_electricity(
            daily("2025-12-31"),
            supply_id="synthetic-power",
            fetched_at=datetime.now(UTC),
        )
        self.client.async_daily_electricity.side_effect = [empty, previous]
        with patch(
            MODULE + "coordinator.dt_util.now",
            return_value=datetime(2026, 1, 1, tzinfo=UTC),
        ):
            await self.refresh()
        self.assertEqual(self.sensor("last_day_date").native_value, date(2025, 12, 31))
        self.assertEqual(
            [
                c.kwargs["year"]
                for c in self.client.async_daily_electricity.await_args_list
            ],
            [2026, 2025],
        )

    async def test_global_outage_hides_all_previous_entities(self):
        await self.refresh()
        self.client.async_supplies.side_effect = TransportError("offline")
        await self.coordinator.async_refresh()
        self.assertFalse(self.coordinator.last_update_success)
        self.assertFalse(self.sensor("supply_status").available)
        self.assertFalse(self.sensor("last_day").available)
        self.assertFalse(self.invoice_sensor("outstanding_amount").available)
        self.assertFalse(self.invoice_sensor("invoice_data_status").available)

    async def test_commissioning_cached_and_ids_stable_across_contract_changes(self):
        await self.refresh()
        await self.refresh()
        self.client.async_commissioning_date.assert_awaited_once()
        self.assertEqual(
            supply_key(self.power),
            supply_key(replace(self.power, contract_id="replacement")),
        )

    async def test_contract_change_invalidates_cached_start_date_without_new_entity(
        self,
    ):
        await self.refresh()
        unique_id = self.sensor("last_day").unique_id
        replacement = replace(
            self.power, contract_id="replacement", activation_date=date(2025, 3, 5)
        )
        self.client.async_supplies.return_value = (replacement, self.gas)
        self.client.async_commissioning_date.return_value = date(2025, 3, 5)
        await self.refresh()
        self.assertEqual(self.client.async_commissioning_date.await_count, 2)
        self.assertEqual(
            self.client.async_daily_electricity.await_args.kwargs["lower_bound"],
            date(2025, 3, 5),
        )
        self.assertEqual(self.sensor("last_day").unique_id, unique_id)
        self.assertEqual(len(self.coordinator._commissioning), 1)

    async def test_commissioning_cache_expires_next_day_and_prunes_removed_supplies(
        self,
    ):
        await self.refresh()
        with patch(
            MODULE + "coordinator.dt_util.now",
            return_value=datetime(2025, 3, 12, tzinfo=UTC),
        ):
            await self.refresh()
        self.assertEqual(self.client.async_commissioning_date.await_count, 2)
        self.client.async_supplies.return_value = (self.gas,)
        await self.refresh()
        self.assertFalse(self.coordinator._commissioning)
        self.assertFalse(self.sensor("last_day").available)

    async def test_corrected_consumption_replaces_old_snapshot_without_accumulation(
        self,
    ):
        await self.refresh()
        corrected = daily()
        period = corrected["consumptionsList"]["years"][0]
        period["totalValue"] = 10
        period["months"][0]["totalValue"] = 5
        period["months"][0]["days"][0]["totalValue"] = 0.75
        self.client.async_daily_electricity.return_value = parse_daily_electricity(
            corrected, supply_id="synthetic-power", fetched_at=datetime.now(UTC)
        )
        await self.refresh()
        self.assertEqual(self.sensor("last_day").native_value, Decimal("0.75"))
        self.assertEqual(self.sensor("month").native_value, Decimal(5))
        self.assertEqual(self.sensor("year").native_value, Decimal(10))
        self.assertEqual(self.sensor("last_day_date").native_value, date(2025, 3, 10))

    async def test_missing_measurement_is_not_zero(self):
        self.client.async_daily_electricity.return_value = parse_daily_electricity(
            daily(rows=[]), supply_id="synthetic-power", fetched_at=datetime.now(UTC)
        )
        await self.refresh()
        self.assertIsNone(self.sensor("last_day").native_value)
        self.assertEqual(self.sensor("data_status").native_value, "no_data")

    async def test_new_supply_creates_entities_without_duplicates(self):
        await self.refresh()
        add = MagicMock()
        await setup_sensors(self.hass, self.entry, add)
        self.assertEqual(len(add.call_args.args[0]), 10 + len(INVOICES))
        self.coordinator.async_update_listeners()
        self.assertEqual(add.call_count, 1)
        other = replace(self.power, point_id="synthetic-other")
        self.client.async_supplies.return_value = (self.power, self.gas, other)
        await self.refresh()
        self.coordinator.async_update_listeners()
        self.assertEqual(len(add.call_args.args[0]), 8)

    async def test_private_atomic_storage_reload_and_remove(self):
        data = credentials(
            "synthetic-key",
            "synthetic-client",
            SessionTokens("access", "refresh", time.time() + 300),
        )
        await async_save_credentials(self.hass, ACCOUNT, data)
        path = Path(credential_store(self.hass, ACCOUNT).path)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.hass.data[STORES].clear()
        self.assertEqual(await async_load_credentials(self.hass, ACCOUNT), data)
        await async_remove_credentials(self.hass, ACCOUNT)
        self.assertFalse(path.exists())

    async def test_failed_disk_write_keeps_rotated_credentials_for_retry(self):
        data = credentials(
            "synthetic-key",
            "synthetic-client",
            SessionTokens("new-access", "new-refresh", time.time() + 300),
        )
        store = credential_store(self.hass, ACCOUNT)
        with patch.object(
            store, "async_save", AsyncMock(side_effect=OSError("disk full"))
        ):
            with self.assertRaises(OSError):
                await async_save_credentials(self.hass, ACCOUNT, data)
        self.assertEqual(await async_load_credentials(self.hass, ACCOUNT), data)

    async def test_invalid_storage_key_cannot_escape_directory(self):
        for key in ("../auth", "a" * 63, None):
            with self.assertRaises(ValueError):
                credential_store(self.hass, key)

    async def test_flow_stores_no_credentials_in_config_entry(self):
        flow = EngieConfigFlow()
        flow.hass = self.hass
        flow.context = {"source": "user"}
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        data = credentials(
            "synthetic-key",
            "synthetic-client",
            SessionTokens("access", "refresh", time.time() + 300),
        )
        flow._authorized = (ACCOUNT, data)
        result = await flow.async_step_finish()
        self.assertEqual(result["data"], {"account_key": ACCOUNT})
        self.assertIsNone(flow._authorized)

    def config_flow(self, **context):
        flow = EngieConfigFlow()
        flow.hass = self.hass
        flow.context = {"source": "user", **context}
        return flow

    async def test_fresh_install_needs_only_official_login_callback(self):
        flow = self.config_flow()
        with patch(MODULE + "config_flow.async_load_credentials", AsyncMock()) as load:
            result = await flow.async_step_user()
        load.assert_not_awaited()
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "authorize")
        self.assertEqual(
            {str(k) for k in result["data_schema"].schema}, {"callback_url"}
        )
        self.assertEqual(
            result["data_schema"].schema["callback_url"].config["autocomplete"], "off"
        )
        self.assertEqual(flow._api_key, "synthetic-app-key")
        self.assertEqual(flow._client_id, DEFAULT_CLIENT_ID)
        self.assertIsNone(flow._authorized)
        self.assertNotIn("synthetic-app-key", str(result))
        self.assertFalse(Path(self.directory.name, ".storage").exists())

    async def test_first_setup_completes_without_files_or_manual_app_parameters(self):
        flow = self.config_flow()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        tokens = SessionTokens(
            "synthetic-access", "synthetic-refresh", time.time() + 300
        )
        await flow.async_step_user()
        with (
            patch(
                MODULE + "config_flow.async_get_clientsession", return_value=object()
            ),
            patch(
                MODULE + "config_flow.async_complete_authorization",
                AsyncMock(return_value=(ACCOUNT, tokens)),
            ) as authorize,
        ):
            result = await flow.async_step_authorize(
                {"callback_url": "synthetic-callback"}
            )
        authorize.assert_awaited_once()
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"], {"account_key": ACCOUNT})
        self.assertEqual(
            await async_load_credentials(self.hass, ACCOUNT),
            credentials("synthetic-app-key", DEFAULT_CLIENT_ID, tokens),
        )
        self.assertIsNone(flow._attempt)
        self.assertIsNone(flow._authorized)
        self.assertIsNone(flow._api_key)

    async def test_new_account_never_reads_another_account_profile_or_tokens(self):
        flow = self.config_flow()
        with (
            patch.object(
                self.hass.config_entries, "async_entries", return_value=[self.entry]
            ),
            patch(MODULE + "config_flow.async_load_credentials", AsyncMock()) as load,
        ):
            result = await flow.async_step_user()
        load.assert_not_awaited()
        self.assertEqual(result["step_id"], "authorize")
        self.assertEqual(flow._client_id, DEFAULT_CLIENT_ID)
        self.assertIsNone(flow._authorized)

    async def test_restart_flow_discards_old_authorization_and_issues_new_attempt(self):
        flow = self.config_flow()
        first = await flow.async_step_user()
        flow._authorized = (ACCOUNT, {"tokens": "old-session"})
        second = await flow.async_step_user()
        self.assertNotEqual(
            first["description_placeholders"], second["description_placeholders"]
        )
        self.assertIsNone(flow._authorized)
        self.assertFalse(Path(self.directory.name, ".storage").exists())

    async def test_authorize_without_attempt_starts_fresh_login(self):
        result = await self.config_flow().async_step_authorize()
        self.assertEqual(result["step_id"], "authorize")
        self.assertIn("authorization_url", result["description_placeholders"])

    async def test_invalid_or_expired_callback_issues_a_fresh_link_without_echo(self):
        flow = self.config_flow()
        first = await flow.async_step_user()
        with (
            patch(
                MODULE + "config_flow.async_get_clientsession", return_value=object()
            ),
            patch(
                MODULE + "config_flow.async_complete_authorization",
                AsyncMock(side_effect=AuthenticationError("rejected")),
            ),
        ):
            result = await flow.async_step_authorize(
                {"callback_url": "private-callback"}
            )
        self.assertEqual(result["errors"], {"base": "invalid_auth"})
        self.assertNotEqual(
            first["description_placeholders"], result["description_placeholders"]
        )
        self.assertNotIn("private-callback", str(result))
        self.assertNotIn("synthetic-app-key", str(result))

    async def test_transport_error_does_not_expose_provider_response(self):
        flow = self.config_flow()
        await flow.async_step_user()
        with (
            patch(
                MODULE + "config_flow.async_get_clientsession", return_value=object()
            ),
            patch(
                MODULE + "config_flow.async_complete_authorization",
                AsyncMock(side_effect=TransportError("private-provider-details")),
            ),
        ):
            result = await flow.async_step_authorize(
                {"callback_url": "private-callback"}
            )
        self.assertEqual(result["errors"], {"base": "retry_authorization"})
        self.assertNotIn("private-", str(result))
        self.assertIsNone(flow._authorized)

    async def test_local_callback_error_preserves_link_and_has_specific_message(self):
        for reason in (
            AuthorizationFailure.INVALID_CALLBACK,
            AuthorizationFailure.STATE_MISMATCH,
        ):
            flow = self.config_flow()
            first = await flow.async_step_user()
            with (
                patch(
                    MODULE + "config_flow.async_get_clientsession",
                    return_value=object(),
                ),
                patch(
                    MODULE + "config_flow.async_complete_authorization",
                    AsyncMock(side_effect=AuthorizationError(reason)),
                ),
            ):
                result = await flow.async_step_authorize(
                    {"callback_url": "private-callback"}
                )
            self.assertEqual(result["errors"], {"base": reason.value})
            self.assertEqual(
                first["description_placeholders"], result["description_placeholders"]
            )
            self.assertNotIn("private-callback", str(result))

    async def test_expired_or_consumed_attempt_is_replaced(self):
        for reason in (
            AuthorizationFailure.EXPIRED,
            AuthorizationFailure.USED,
            AuthorizationFailure.TOKEN_EXCHANGE,
            AuthorizationFailure.IDENTITY,
            AuthorizationFailure.SESSION,
        ):
            flow = self.config_flow()
            first = await flow.async_step_user()
            flow._attempt.consumed = reason not in {
                AuthorizationFailure.EXPIRED,
                AuthorizationFailure.USED,
            }
            with (
                patch(
                    MODULE + "config_flow.async_get_clientsession",
                    return_value=object(),
                ),
                patch(
                    MODULE + "config_flow.async_complete_authorization",
                    AsyncMock(side_effect=AuthorizationError(reason)),
                ),
            ):
                result = await flow.async_step_authorize(
                    {"callback_url": "private-callback"}
                )
            self.assertEqual(result["errors"], {"base": reason.value})
            self.assertNotEqual(
                first["description_placeholders"], result["description_placeholders"]
            )

    async def test_reauth_preserves_own_profile_and_requires_same_account(self):
        data = credentials(
            "own-key", "own-client", SessionTokens("a", "r", time.time() + 300)
        )
        flow = self.config_flow(source="reauth")
        with patch(
            MODULE + "config_flow.async_load_credentials", AsyncMock(return_value=data)
        ):
            result = await flow.async_step_reauth(self.entry.data)
        self.assertEqual(result["step_id"], "reauth_confirm")
        self.assertEqual(
            (await flow.async_step_reauth_confirm({}))["step_id"], "authorize"
        )
        self.assertEqual(flow._api_key, "own-key")
        self.assertEqual(flow._client_id, "own-client")
        self.assertIsNone(flow._authorized)

    async def test_missing_reauth_store_uses_builtin_profile_without_account_restore(
        self,
    ):
        flow = self.config_flow(source="reauth")
        with patch(
            MODULE + "config_flow.async_load_credentials",
            AsyncMock(side_effect=ValueError),
        ):
            result = await flow.async_step_reauth(self.entry.data)
        self.assertEqual(result["step_id"], "authorize")
        self.assertEqual(flow._api_key, "synthetic-app-key")
        self.assertIsNone(flow._authorized)
        self.assertEqual(flow.context["source"], "reauth")
        self.assertFalse(Path(self.directory.name, ".storage").exists())

    async def test_finish_storage_retry_does_not_repeat_provider_login(self):
        flow = self.config_flow()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        data = credentials(
            "synthetic-app-key",
            DEFAULT_CLIENT_ID,
            SessionTokens("a", "r", time.time() + 300),
        )
        flow._authorized = (ACCOUNT, data)
        with patch(
            MODULE + "config_flow.async_save_credentials",
            AsyncMock(side_effect=OSError),
        ):
            result = await flow.async_step_finish()
        self.assertEqual(result["errors"], {"base": "storage_error"})
        self.assertIsNotNone(flow._authorized)
        result = await flow.async_step_finish({})
        self.assertEqual(result["type"], "create_entry")
        self.assertIsNone(flow._authorized)

    async def test_reauth_cannot_replace_another_account(self):
        flow = EngieConfigFlow()
        flow.hass = self.hass
        flow.context = {"source": "reauth"}
        flow.async_set_unique_id = AsyncMock()
        flow._get_reauth_entry = MagicMock(return_value=self.entry)
        flow._authorized = ("b" * 64, {})
        result = await flow.async_step_finish()
        self.assertEqual(result["reason"], "wrong_account")
        self.assertFalse(Path(self.directory.name, ".storage").exists())

    async def test_diagnostics_are_allowlisted(self):
        await self.refresh()
        result = await async_get_config_entry_diagnostics(self.hass, self.entry)
        serialized = json.dumps(result)
        for private in (
            "synthetic",
            "access_token",
            "refresh_token",
            ACCOUNT,
            "1.25",
            "7.31",
        ):
            self.assertNotIn(private, serialized)


class MetadataTests(unittest.TestCase):
    def test_translations_and_manifest(self):
        root = Path(__file__).resolve().parents[1]
        integration = root / "custom_components" / "engie_italia"
        manifest = json.loads((integration / "manifest.json").read_text())
        self.assertTrue(manifest["config_flow"])
        source = json.loads((integration / "strings.json").read_text())
        self.assertEqual(
            source, json.loads((integration / "translations/en.json").read_text())
        )
        italian = json.loads((integration / "translations/it.json").read_text())
        for section in ("config", "options", "entity"):
            self.assertEqual(source[section].keys(), italian[section].keys())
        self.assertEqual(
            source["config"]["step"].keys(), italian["config"]["step"].keys()
        )
        self.assertNotIn("file_upload", manifest.get("dependencies", []))
        self.assertFalse(any("pyaxmlparser" in r for r in manifest["requirements"]))
        for language in (source, italian):
            for reason in AuthorizationFailure:
                self.assertIn(reason.value, language["config"]["error"])
            self.assertEqual(
                set(language["config"]["step"]),
                {"authorize", "finish", "reauth_confirm"},
            )
            authorize = language["config"]["step"]["authorize"]
            self.assertEqual(set(authorize["data"]), {"callback_url"})
            self.assertIn("callback_url", authorize["data_description"])
            self.assertIn("{authorization_url}", authorize["description"])
            self.assertIn(
                "https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/SETUP.md",
                authorize["description"],
            )

    def test_setup_copy_describes_user_actions_without_implementation_details(self):
        root = Path(__file__).resolve().parents[1] / "custom_components/engie_italia"

        def text_values(value):
            if isinstance(value, dict):
                for child in value.values():
                    yield from text_values(child)
            elif isinstance(value, str):
                yield value

        for filename in (
            "strings.json",
            "translations/en.json",
            "translations/it.json",
        ):
            config = json.loads((root / filename).read_text())["config"]
            visible = " ".join(text_values(config)).lower()
            for term in ("apk", "api", "oauth", "pkce", "token", "code=", "state="):
                self.assertNotIn(term, visible)
            description = config["step"]["authorize"]["description"]
            self.assertEqual(
                [
                    line[:2]
                    for line in description.splitlines()
                    if line[:2] in {"1.", "2.", "3."}
                ],
                ["1.", "2.", "3."],
            )
            self.assertIn("10 minut", description)

    def test_local_brand_images_and_retina_dimensions(self):
        folder = (
            Path(__file__).resolve().parents[1] / "custom_components/engie_italia/brand"
        )
        for theme in ("", "dark_"):
            for kind in ("icon", "logo"):
                dimensions = []
                for retina in ("", "@2x"):
                    data = (folder / f"{theme}{kind}{retina}.png").read_bytes()
                    self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                    width, height = struct.unpack(">II", data[16:24])
                    dimensions.append((width, height))
                    self.assertEqual(data[25], 6, "Expected RGBA transparency")
                    if kind == "icon":
                        self.assertEqual(width, height)
                    self.assertEqual(min(width, height), 512 if retina else 256)
                self.assertEqual(dimensions[1], tuple(d * 2 for d in dimensions[0]))

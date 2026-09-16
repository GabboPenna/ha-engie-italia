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
from pathlib import Path
from types import MappingProxyType
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from mobile_fixtures import daily, supplies  # noqa: E402

from custom_components.engie_italia.api.client import EngieMobileClient  # noqa: E402
from custom_components.engie_italia.api.errors import (  # noqa: E402
    AuthenticationError,
    TransportError,
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
        self.client.lower_bound = EngieMobileClient.lower_bound
        self.coordinator = EngieCoordinator(self.hass, self.entry, self.client)
        self.entry.runtime_data = self.coordinator
        self.clock = patch(
            MODULE + "coordinator.dt_util.now",
            return_value=datetime(2025, 3, 11, tzinfo=UTC),
        )
        self.clock.start()

    async def asyncTearDown(self):
        self.clock.stop()
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

    async def test_commissioning_cached_and_ids_stable_across_contract_changes(self):
        await self.refresh()
        await self.refresh()
        self.client.async_commissioning_date.assert_awaited_once()
        self.assertEqual(
            supply_key(self.power),
            supply_key(replace(self.power, contract_id="replacement")),
        )

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
        self.assertEqual(len(add.call_args.args[0]), 10)
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

    async def test_welcome_has_login_and_separate_advanced_connection(self):
        result = await self.config_flow().async_step_user()
        self.assertEqual(result["type"], "menu")
        self.assertEqual(result["menu_options"], ["connect", "api_setup"])
        self.assertEqual(
            {str(k) for k in result["data_schema"].schema}, {"next_step_id"}
        )

    async def test_first_install_requires_key_but_hides_client_id(self):
        flow = self.config_flow()
        result = await flow.async_step_connect()
        self.assertEqual(result["step_id"], "api_setup")
        self.assertEqual(
            {str(k) for k in result["data_schema"].schema}, {"api_key", "oauth"}
        )
        self.assertTrue(result["data_schema"].schema["oauth"].options["collapsed"])
        result = await flow.async_step_api_setup({"api_key": "synthetic-key"})
        self.assertEqual(result["step_id"], "authorize")
        self.assertEqual(flow._client_id, DEFAULT_CLIENT_ID)
        self.assertEqual(
            {str(k) for k in result["data_schema"].schema}, {"callback_url"}
        )
        self.assertNotIn("synthetic-key", str(result))

    async def test_advanced_client_override_and_invalid_key(self):
        flow = self.config_flow()
        result = await flow.async_step_api_setup()
        self.assertIn(
            "client_id",
            {str(k) for k in result["data_schema"].schema["oauth"].schema.schema},
        )
        result = await flow.async_step_api_setup({"api_key": ""})
        self.assertEqual(result["errors"], {"base": "invalid_config"})
        result = await flow.async_step_api_setup(
            {"api_key": "synthetic-key", "oauth": {"client_id": "custom-client"}}
        )
        self.assertEqual(result["step_id"], "authorize")
        self.assertEqual(flow._client_id, "custom-client")

    async def test_reuse_only_api_profile_with_new_authorization(self):
        data = credentials(
            "synthetic-key",
            "synthetic-client",
            SessionTokens("old-access", "old-refresh", time.time() + 300),
        )
        flow = self.config_flow()
        with (
            patch.object(
                self.hass.config_entries, "async_entries", return_value=[self.entry]
            ),
            patch(
                MODULE + "config_flow.async_load_credentials",
                AsyncMock(return_value=data),
            ),
        ):
            result = await flow.async_step_connect()
        self.assertEqual(result["step_id"], "authorize")
        self.assertEqual(flow._api_key, "synthetic-key")
        self.assertEqual(flow._client_id, "synthetic-client")
        self.assertIsNone(flow._authorized)
        self.assertIsNotNone(flow._attempt)
        for secret in ("synthetic-key", "old-access", "old-refresh"):
            self.assertNotIn(secret, str(result))
        for token in ("old-access", "old-refresh"):
            self.assertNotIn(token, str(vars(flow)))

    async def test_damaged_or_ambiguous_profiles_require_explicit_setup(self):
        def profile(key):
            return credentials(
                key, "client", SessionTokens("a", "r", time.time() + 300)
            )

        cases = [
            ([ValueError("missing")], "api_setup"),
            ([OSError("unreadable")], "api_setup"),
            ([profile("first"), profile("second")], "api_setup"),
            ([profile("same"), profile("same")], "authorize"),
            ([ValueError("missing"), profile("valid")], "authorize"),
        ]
        for responses, step in cases:
            with (
                self.subTest(step=step, profiles=len(responses)),
                patch.object(
                    self.hass.config_entries,
                    "async_entries",
                    return_value=[self.entry] * len(responses),
                ),
                patch(
                    MODULE + "config_flow.async_load_credentials",
                    AsyncMock(side_effect=responses),
                ),
            ):
                self.assertEqual(
                    (await self.config_flow().async_step_connect())["step_id"], step
                )

    async def test_reauth_uses_own_profile_or_requests_repair(self):
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
        with patch(
            MODULE + "config_flow.async_load_credentials",
            AsyncMock(side_effect=ValueError),
        ):
            result = await self.config_flow(source="reauth").async_step_reauth(
                self.entry.data
            )
        self.assertEqual(result["step_id"], "api_setup")

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
        for language in (source, italian):
            menu = language["config"]["step"]["user"]["menu_options"]
            self.assertEqual(set(menu), {"connect", "api_setup"})
            self.assertIn(
                "{authorization_url}",
                language["config"]["step"]["authorize"]["description"],
            )

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

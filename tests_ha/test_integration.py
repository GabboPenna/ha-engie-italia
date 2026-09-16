"""Real HA framework with temporary storage and exclusively invented account data."""

import json
import stat
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

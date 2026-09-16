"""Read-only ENGIE Italia beta integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import EngieMobileClient
from .api.session import SessionTokens
from .const import CONF_ACCOUNT_KEY, DOMAIN
from .coordinator import EngieCoordinator
from .storage import (
    async_load_credentials,
    async_remove_credentials,
    async_save_credentials,
)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass, entry: ConfigEntry):
    account_key = entry.data[CONF_ACCOUNT_KEY]
    try:
        data = await async_load_credentials(hass, account_key)
    except ValueError as error:
        raise ConfigEntryAuthFailed("ENGIE authorization is required") from error
    except Exception as error:
        raise ConfigEntryNotReady("Cannot read the stored ENGIE session") from error
    tokens = SessionTokens.from_storage(data["tokens"])

    async def persist(updated: SessionTokens):
        replacement = {**data, "tokens": updated.as_storage()}
        await async_save_credentials(hass, account_key, replacement)
        data.update(replacement)

    client = EngieMobileClient(
        async_get_clientsession(hass),
        api_key=data["api_key"],
        client_id=data["client_id"],
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.remaining_seconds,
        token_updated=persist,
    )
    coordinator = EngieCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.unique_id)},
        name="ENGIE Italia",
        manufacturer="ENGIE",
        model="Account",
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.async_shutdown()
    entry.runtime_data.client.clear_credentials()
    return True


async def async_remove_entry(hass, entry):
    await async_remove_credentials(hass, entry.data[CONF_ACCOUNT_KEY])

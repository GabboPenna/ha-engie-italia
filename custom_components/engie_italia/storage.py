"""Atomic private HA storage; not an encrypted vault or diagnostic payload."""

import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .api.session import SessionTokens, credential
from .const import DOMAIN

STORES = f"{DOMAIN}_stores"
PENDING = f"{DOMAIN}_pending_credentials"


def credential_store(hass: HomeAssistant, account_key: str) -> Store:
    if not isinstance(account_key, str) or not re.fullmatch(
        r"[0-9a-f]{64}", account_key
    ):
        raise ValueError("Invalid account storage key")
    stores = hass.data.setdefault(STORES, {})
    if account_key not in stores:
        stores[account_key] = Store(
            hass, 1, f"{DOMAIN}.auth.{account_key}", private=True, atomic_writes=True
        )
    return stores[account_key]


async def async_save_credentials(hass, account_key: str, data: dict):
    store = credential_store(hass, account_key)
    validated = validate_credentials(data)
    pending = hass.data.setdefault(PENDING, {})
    pending[account_key] = validated
    await store.async_save(validated)
    if pending.get(account_key) is validated:
        pending.pop(account_key)


async def async_load_credentials(hass, account_key: str) -> dict:
    store = credential_store(hass, account_key)
    pending = hass.data.setdefault(PENDING, {})
    if account_key in pending:
        await async_save_credentials(hass, account_key, pending[account_key])
    return validate_credentials(await store.async_load())


async def async_remove_credentials(hass, account_key: str):
    await credential_store(hass, account_key).async_remove()
    hass.data.get(PENDING, {}).pop(account_key, None)
    hass.data.get(STORES, {}).pop(account_key, None)


def credentials(api_key: str, client_id: str, tokens: SessionTokens) -> dict:
    return {
        "api_key": credential(api_key),
        "client_id": credential(client_id),
        "tokens": tokens.as_storage(),
    }


def validate_credentials(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Missing stored credentials")
    return credentials(
        data.get("api_key"),
        data.get("client_id"),
        SessionTokens.from_storage(data.get("tokens")),
    )

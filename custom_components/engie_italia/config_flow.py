"""Assisted browser authorization and account-safe reauthentication."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api.app import DEFAULT_API_KEY
from .api.auth import AuthorizationAttempt, async_complete_authorization
from .api.errors import (
    AuthenticationError,
    AuthorizationError,
    AuthorizationFailure,
    EngieError,
)
from .const import (
    CONF_ACCOUNT_KEY,
    CONF_API_KEY,
    CONF_CALLBACK,
    CONF_CLIENT_ID,
    CONF_INTERVAL,
    DEFAULT_CLIENT_ID,
    DEFAULT_INTERVAL_HOURS,
    DOMAIN,
)
from .storage import async_load_credentials, async_save_credentials, credentials

_LOGGER = logging.getLogger(__name__)


class EngieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._api_key = None
        self._client_id = DEFAULT_CLIENT_ID
        self._attempt = None
        self._authorized = None

    async def async_step_user(self, user_input=None):
        return await self.async_step_connect()

    async def async_step_connect(self, user_input=None):
        # Application parameters are shared; every account needs its own consent.
        self._api_key = DEFAULT_API_KEY
        self._client_id = DEFAULT_CLIENT_ID
        self._authorized = None
        self._attempt = AuthorizationAttempt(self._client_id)
        return await self.async_step_authorize()

    async def async_step_authorize(self, user_input=None):
        errors = {}
        if self._attempt is None:
            return await self.async_step_user()
        if user_input is not None:
            restart = False
            try:
                account_key, tokens = await async_complete_authorization(
                    async_get_clientsession(self.hass),
                    self._attempt,
                    user_input.get(CONF_CALLBACK),
                )
            except AuthorizationError as err:
                errors["base"] = err.reason.value
                restart = err.reason in {
                    AuthorizationFailure.EXPIRED,
                    AuthorizationFailure.USED,
                    AuthorizationFailure.DENIED,
                }
                _LOGGER.warning("ENGIE sign-in failed: %s", err.reason.value)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
                restart = True
                _LOGGER.warning("ENGIE sign-in failed: authentication")
            except EngieError:
                errors["base"] = (
                    "cannot_connect"
                    if self._attempt.consumed
                    else "retry_authorization"
                )
                _LOGGER.warning("ENGIE sign-in failed: %s", errors["base"])
            else:
                self._authorized = (
                    account_key,
                    credentials(self._api_key, self._client_id, tokens),
                )
                return await self.async_step_finish()
            if restart or self._attempt.consumed or self._attempt.expired:
                self._attempt = AuthorizationAttempt(self._client_id)
        return self.async_show_form(
            step_id="authorize",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CALLBACK): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.PASSWORD, autocomplete="off"
                        )
                    )
                }
            ),
            description_placeholders={
                "authorization_url": self._attempt.authorization_url,
                "setup_url": "https://github.com/GabboPenna/ha-engie-italia/blob/main/docs/SETUP.md",
            },
        )

    async def async_step_finish(self, user_input=None):
        if self._authorized is None:
            return self.async_abort(reason="authorization_expired")
        account_key, data = self._authorized
        await self.async_set_unique_id(account_key)
        reauth = self.context.get("source") == config_entries.SOURCE_REAUTH
        if reauth:
            entry = self._get_reauth_entry()
            if entry.unique_id != account_key:
                self._authorized = None
                return self.async_abort(reason="wrong_account")
        else:
            self._abort_if_unique_id_configured()
        try:
            await async_save_credentials(self.hass, account_key, data)
        except Exception:
            # Preserve the just-issued session in memory so a local retry is safe.
            return self.async_show_form(
                step_id="finish",
                data_schema=vol.Schema({}),
                errors={"base": "storage_error"},
            )
        self._authorized = None
        self._api_key = None
        self._attempt = None
        if reauth:
            return self.async_update_reload_and_abort(
                entry, data_updates={CONF_ACCOUNT_KEY: account_key}
            )
        return self.async_create_entry(
            title="ENGIE Italia", data={CONF_ACCOUNT_KEY: account_key}
        )

    async def async_step_reauth(self, entry_data):
        try:
            data = await async_load_credentials(self.hass, entry_data[CONF_ACCOUNT_KEY])
            self._api_key, self._client_id = data[CONF_API_KEY], data[CONF_CLIENT_ID]
        except (ValueError, KeyError, OSError):
            return await self.async_step_user()
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        if user_input is not None:
            self._attempt = AuthorizationAttempt(self._client_id)
            return await self.async_step_authorize()
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=vol.Schema({})
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EngieOptionsFlow()


class EngieOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_INTERVAL, DEFAULT_INTERVAL_HOURS
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
                }
            ),
        )

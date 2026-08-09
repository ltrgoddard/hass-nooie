"""Config flow for Nooie: take the account login and list its cameras."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from . import proxy
from .const import CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_COUNTRY_CODE, default=DEFAULT_COUNTRY_CODE): str,
    }
)


class NooieConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nooie."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect the Nooie account login."""
        return await self._async_step_account("user", user_input, {})

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the login of an existing entry."""
        return await self._async_step_account(
            "reconfigure", user_input, dict(self._get_reconfigure_entry().data)
        )

    async def _async_step_account(
        self,
        step_id: str,
        user_input: dict[str, Any] | None,
        defaults: dict[str, Any],
    ) -> ConfigFlowResult:
        """Sign in, and keep the login once it lists at least one camera."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                devices = await proxy.async_devices(self.hass, user_input)
            except proxy.ProxyError as error:
                _LOGGER.debug("Nooie sign-in failed: %s", error)
                rejected = "login failed" in str(error)
                errors["base"] = (
                    "invalid_auth" if rejected else "cannot_connect"
                )
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    return await self._async_finish(user_input)
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(
                SCHEMA, user_input or defaults
            ),
            errors=errors,
        )

    async def _async_finish(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create the entry, or write the new login into the old one."""
        await self.async_set_unique_id(str(data[CONF_USERNAME]).casefold())
        if self.source == SOURCE_RECONFIGURE:
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(), data=data
            )
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=str(data[CONF_USERNAME]), data=data
        )

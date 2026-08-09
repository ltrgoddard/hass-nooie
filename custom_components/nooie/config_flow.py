"""Config flow for Nooie: point at the add-on's go2rtc server and verify it."""

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant

from .const import CONF_URL, DEFAULT_URL, DOMAIN
from .util import api_url, is_nooie_stream


async def _check(hass: HomeAssistant, url: str) -> str | None:
    """Return an error key, or None when the server has Nooie streams."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    session = async_get_clientsession(hass)
    try:
        async with session.get(api_url(url), timeout=10) as response:
            if response.status != 200:
                return "cannot_connect"
            data = await response.json(content_type=None)
    except Exception:
        return "cannot_connect"
    streams = data if isinstance(data, dict) else {}
    if not any(is_nooie_stream(name) for name in streams):
        return "no_streams"
    return None


class NooieConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nooie."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect the go2rtc URL."""
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            if (error := await _check(self.hass, url)) is not None:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title="Nooie", data={CONF_URL: url}
                )
        data_schema = vol.Schema(
            {vol.Required(CONF_URL, default=DEFAULT_URL): str}
        )
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the go2rtc URL of an existing entry."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            if (error := await _check(self.hass, url)) is not None:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    entry, data={CONF_URL: url}
                )
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_URL, default=entry.data.get(CONF_URL, DEFAULT_URL)
                ): str
            }
        )
        return self.async_show_form(
            step_id="reconfigure", data_schema=data_schema, errors=errors
        )

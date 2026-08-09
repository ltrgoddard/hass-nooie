"""The Nooie integration: camera entities fed by the nooie-proxy engine."""

from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from . import proxy

PLATFORMS = [Platform.CAMERA]

type NooieConfigEntry = ConfigEntry[NooieAccount]


@dataclass(frozen=True)
class NooieAccount:
    """The cameras on the account, and the port that serves them."""

    devices: dict[str, dict[str, Any]]
    port: int

    def stream_url(self, device_id: str) -> str:
        """Where a reader finds this camera's MPEG-TS."""
        return f"http://127.0.0.1:{self.port}/{device_id}"


async def async_setup_entry(
    hass: HomeAssistant, entry: NooieConfigEntry
) -> bool:
    """Set up Nooie from a config entry.

    The account is read once. Each read is a sign-in, and Nooie limits the
    rate of those, so reload the entry to pick up a camera you have added.
    """
    try:
        # The first time, this builds the proxy's environment, which takes
        # a minute or two; afterwards it is a version check.
        python = await proxy.async_prepare(hass)
        devices = await proxy.async_devices(hass, python, entry.data)
    except proxy.ProxyError as error:
        raise ConfigEntryNotReady(str(error)) from error
    entry.runtime_data = NooieAccount(
        devices, await proxy.async_serve(hass, entry, python, devices)
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: NooieConfigEntry
) -> bool:
    """Unload a config entry; the loopback server closes with it."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

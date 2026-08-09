"""Coordinator: watch the add-on's go2rtc server for Nooie streams."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_URL, DOMAIN, SCAN_INTERVAL
from .util import api_url, is_nooie_stream

_LOGGER = logging.getLogger(__name__)


class NooieCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Poll /api/streams and keep the set of Nooie streams current."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)

    @property
    def base_url(self) -> str:
        """The configured go2rtc base URL."""
        return str(self.entry.data[CONF_URL])

    async def _async_update_data(self) -> dict[str, dict]:
        """Fetch the stream list and keep only the add-on's cameras."""
        async with self._session.get(
            api_url(self.api_url), timeout=10
        ) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)
        streams = data if isinstance(data, dict) else {}
        return {
            name: info
            for name, info in streams.items()
            if is_nooie_stream(name)
        }

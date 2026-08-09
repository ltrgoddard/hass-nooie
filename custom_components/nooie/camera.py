"""Camera entities for the Nooie integration."""

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NooieAccount, NooieConfigEntry
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NooieConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add a camera for each camera on the account."""
    account = entry.runtime_data
    async_add_entities(
        NooieCamera(account, device_id) for device_id in account.devices
    )


class NooieCamera(Camera):
    """One Nooie camera, streamed by its own nooie-proxy process."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, account: NooieAccount, device_id: str) -> None:
        super().__init__()
        self._account = account
        self._device_id = device_id
        self._attr_unique_id = device_id
        device = account.devices[device_id]
        # A camera that was off when the account was read is not called, so
        # it has nothing to show until the entry is reloaded.
        self._attr_available = bool(device.get("online"))
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Nooie",
            model=device["model"],
            name=device["name"],
        )

    @property
    def use_stream_for_stills(self) -> bool:
        """Stills come from the same stream, so nothing else opens a call."""
        return True

    async def stream_source(self) -> str:
        """The loopback URL that carries this camera's MPEG-TS."""
        return self._account.stream_url(self._device_id)

"""Camera entities for the Nooie integration."""

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NooieCoordinator
from .util import friendly_name, rtsp_url


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add a camera entity for each Nooie stream the add-on publishes."""
    coordinator: NooieCoordinator = hass.data[DOMAIN][entry.entry_id]
    added: set[str] = set()

    def add_cameras() -> None:
        new = [name for name in coordinator.data if name not in added]
        if not new:
            return
        added.update(new)
        async_add_entities(NooieCamera(coordinator, name) for name in new)

    add_cameras()
    coordinator.async_add_listener(add_cameras)


class NooieCamera(CoordinatorEntity[NooieCoordinator], Camera):
    """A camera whose stream comes from the Nooie add-on's go2rtc server."""

    _attr_has_entity_name = True
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, coordinator: NooieCoordinator, stream_name: str) -> None:
        # CoordinatorEntity subscribes the entity to coordinator updates, so
        # availability follows the stream list; Camera needs its own __init__.
        super().__init__(coordinator)
        Camera.__init__(self)
        # Not "self.stream": Camera uses that for the stream component's
        # Stream object, and overwriting it breaks streaming.
        self._stream_name = stream_name
        self._attr_unique_id = f"{DOMAIN}-{stream_name}"
        self._attr_name = friendly_name(stream_name)

    @property
    def use_stream_for_stills(self) -> bool:
        """Stills come from the same stream, so nothing else reads it."""
        return True

    @property
    def available(self) -> bool:
        """Only available while the add-on publishes this stream."""
        return self._stream_name in self.coordinator.data

    async def stream_source(self) -> str:
        """The RTSP endpoint on the add-on's go2rtc server."""
        return rtsp_url(self.coordinator.base_url, self._stream_name)

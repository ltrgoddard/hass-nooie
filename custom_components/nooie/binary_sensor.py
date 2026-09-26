"""Motion and crying sensors, from the alerts the Nooie app shows."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from . import NooieConfigEntry
from .const import DOMAIN
from .proxy import signal

# An alert is a moment, not a state: hold it on for long enough to act on.
HOLD = 30
KINDS = {
    "motion": BinarySensorDeviceClass.MOTION,
    "cry": BinarySensorDeviceClass.SOUND,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NooieConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add a motion and a crying sensor for each camera on the account."""
    async_add_entities(
        NooieAlert(device_id, kind)
        for device_id in entry.runtime_data.devices
        for kind in KINDS
    )


class NooieAlert(BinarySensorEntity):
    """On for a while after the camera raises an alert of one kind."""

    _attr_has_entity_name = True
    _attr_is_on = False
    _off: CALLBACK_TYPE | None = None

    def __init__(self, device_id: str, kind: str) -> None:
        self._device_id = device_id
        self._kind = kind
        self._attr_unique_id = f"{device_id}_{kind}"
        self._attr_device_class = KINDS[kind]
        self._attr_translation_key = kind
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def async_added_to_hass(self) -> None:
        """Listen for this camera's alerts."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal(self._device_id), self._alert
            )
        )
        self.async_on_remove(lambda: self._off and self._off())

    @callback
    def _alert(self, kind: str) -> None:
        if kind != self._kind:
            return
        if self._off:
            self._off()
        self._attr_is_on = True
        self._off = async_call_later(self.hass, HOLD, self._clear)
        self.async_write_ha_state()

    @callback
    def _clear(self, _now) -> None:
        self._off = None
        self._attr_is_on = False
        self.async_write_ha_state()

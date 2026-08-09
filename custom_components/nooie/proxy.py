"""Run nooie-proxy, and carry what it prints on a loopback HTTP port.

Home Assistant runs go2rtc itself, but it lets go2rtc execute the ffmpeg
binary and nothing else, so an `exec:` source is not available to us. An
HTTP source is: go2rtc reads MPEG-TS over HTTP, and so does the stream
component. One port therefore serves the live view, the snapshots, and any
other consumer, without a second copy of go2rtc.

A call takes 10 to 20 seconds to answer, and a reader gives up before then,
so each camera holds one call open for as long as the entry is loaded. A
reader joins the stream that is already running.
"""

import asyncio
import contextlib
import logging
import os
import sys
from functools import partial
from pathlib import Path
from typing import Any

from aiohttp import web
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_COUNTRY_CODE, DOMAIN

_LOGGER = logging.getLogger(__name__)

# A reader has to see a transport packet from its first byte, so read whole
# packets: the muxer writes them from byte zero, and this keeps that phase.
PACKET = 188
CHUNK = PACKET * 32
# What a reader may fall behind by before it loses a moment of the stream.
BACKLOG = 64
# A sign-in, the device list, and a slow cloud: generous, but bounded.
LIST_TIMEOUT = 90
# How long a proxy has to hang up its call before it is killed.
CLOSE_TIMEOUT = 5
# How long to wait before placing a dropped call again, how long a call has
# to last to count as one that worked, and how far the wait backs off for a
# camera that never answers. Each attempt is a sign-in, and Nooie limits the
# rate of those, so a camera that is off must not become a sign-in loop.
RETRY = 30
STEADY = 60
MAX_RETRY = 600
# The proxy's own environment. It is a program, not a library: Home Assistant
# pins the versions an integration's requirements resolve against, PyAV among
# them, and the proxy needs a newer one than the pin. Giving it an environment
# of its own settles that at this release and at every later one, and costs
# far less disk than the container this integration replaced.
VERSION = "0.2.0"
PACKAGE = f"nooie-proxy=={VERSION}"
BUILD_TIMEOUT = 900
# aiortc reads crc32c only for SCTP, which a receive-only call never opens.
# The pure-python fallback therefore costs nothing here, but it warns once
# per process. Keep that one warning out of the log; the rest still show.
QUIET = "ignore::RuntimeWarning:google_crc32c"


class ProxyError(Exception):
    """nooie-proxy did not run, or the account did not answer."""


async def _output(*args: str, timeout: int) -> tuple[int, str]:
    """Run a command to the end and return its code and what it said."""
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except OSError as error:
        # The environment is not built yet, or no longer runs.
        return 1, str(error)
    try:
        async with asyncio.timeout(timeout):
            stdout, _ = await process.communicate()
    except TimeoutError:
        process.kill()
        return 1, "timed out"
    return process.returncode or 0, stdout.decode(errors="replace").strip()


async def _installed(python: str) -> str:
    """The proxy version in that environment, or nothing at all."""
    code, said = await _output(
        python,
        "-c",
        "from importlib.metadata import version; print(version('nooie-proxy'))",
        timeout=60,
    )
    return said if code == 0 else ""


async def async_prepare(hass: HomeAssistant) -> str:
    """The interpreter that runs the proxy, built the first time it is asked."""
    root = Path(hass.config.path(DOMAIN, "venv"))
    python = str(root / "bin" / "python")
    if await _installed(python) == VERSION:
        return python
    _LOGGER.info("Building the nooie-proxy environment in %s", root)
    for command in (
        (sys.executable, "-m", "venv", "--clear", str(root)),
        (python, "-m", "pip", "install", "--no-input", "--quiet", PACKAGE),
    ):
        code, said = await _output(*command, timeout=BUILD_TIMEOUT)
        if code != 0:
            raise ProxyError(f"could not install {PACKAGE}: {said[-400:]}")
    if await _installed(python) != VERSION:
        raise ProxyError(f"{PACKAGE} did not install")
    _LOGGER.info("Installed %s", PACKAGE)
    return python


async def _spawn(
    hass: HomeAssistant,
    python: str,
    data: dict[str, Any],
    *args: str,
    device_id: str = "",
) -> asyncio.subprocess.Process:
    """Run nooie-proxy in its own environment.

    The credentials reach the process through its environment, so they are
    never written to a file that a backup would carry off the machine.
    """
    home = hass.config.path(DOMAIN, device_id or "account")
    return await asyncio.create_subprocess_exec(
        python,
        "-m",
        "nooie_proxy",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=os.environ
        | {
            # The proxy keeps the UUID that names this install here, and the
            # session it signed in with, so a rebuilt container signs in as
            # the same client as before. Each camera gets a directory of its
            # own, because Nooie's signalling holds one websocket for each
            # install: a second connection closes the first, and the call it
            # was carrying ends. Cameras that shared an install would take
            # turns streaming for a few seconds each. HOME as well as
            # XDG_CONFIG_HOME, because macOS reads only the first.
            "HOME": home,
            "XDG_CONFIG_HOME": home,
            "PYTHONWARNINGS": QUIET,
            "NOOIE_USERNAME": str(data[CONF_USERNAME]),
            "NOOIE_PASSWORD": str(data[CONF_PASSWORD]),
            "NOOIE_COUNTRY_CODE": str(data[CONF_COUNTRY_CODE]),
            "NOOIE_DEVICE_ID": device_id,
        },
    )


async def _log(stderr: asyncio.StreamReader) -> str:
    """Drain the proxy's progress, and keep its last word.

    Draining is not optional: a full stderr pipe would stall the proxy.
    """
    said = ""
    async for line in stderr:
        said = line.decode(errors="replace").rstrip()
        _LOGGER.debug("nooie-proxy: %s", said)
    return said


async def _close(process: asyncio.subprocess.Process) -> None:
    """Ask the proxy to hang up the call, and insist if it does not."""
    with contextlib.suppress(ProcessLookupError):
        process.terminate()
    try:
        async with asyncio.timeout(CLOSE_TIMEOUT):
            await process.wait()
    except TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            process.kill()
        await process.wait()


async def async_devices(
    hass: HomeAssistant, python: str, data: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Every camera on the account, keyed by UUID."""
    process = await _spawn(hass, python, data, "--list-devices")
    try:
        async with asyncio.timeout(LIST_TIMEOUT):
            stdout, stderr = await process.communicate()
    except TimeoutError as error:
        process.kill()
        raise ProxyError("nooie-proxy did not answer") from error
    if process.returncode:
        said = stderr.decode(errors="replace").splitlines()
        lines = [line.strip() for line in said if line.strip()]
        raise ProxyError(lines[-1] if lines else "nooie-proxy failed")
    found: dict[str, dict[str, Any]] = {}
    for line in stdout.decode(errors="replace").splitlines():
        fields = line.split("\t")
        if len(fields) == 4 and fields[0] != "uuid":
            uuid, name, model, online = fields
            found[uuid] = {
                "name": name,
                "model": model,
                "online": online == "yes",
            }
    return found


class Feed:
    """One camera's call, held open and fanned out to its readers."""

    def __init__(
        self,
        hass: HomeAssistant,
        python: str,
        data: dict[str, Any],
        device_id: str,
        name: str,
    ) -> None:
        self._hass = hass
        self._python = python
        self._data = data
        self._device_id = device_id
        self._name = name or device_id
        self._readers: set[asyncio.Queue[bytes]] = set()
        self._process: asyncio.subprocess.Process | None = None
        self._task = asyncio.create_task(
            self._call(), name=f"nooie {device_id}"
        )

    async def async_close(self) -> None:
        """Hang up at once.

        The polite goodbye belongs to a call that ended on its own. This one
        runs while Home Assistant is stopping, which will not wait: anything
        left behind here is a proxy that goes on calling a camera forever.
        """
        self._task.cancel()
        if self._process is not None:
            with contextlib.suppress(ProcessLookupError):
                self._process.kill()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task

    @contextlib.asynccontextmanager
    async def reader(self):
        """A queue of packet-aligned chunks, for as long as it is read."""
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=BACKLOG)
        self._readers.add(queue)
        try:
            yield queue
        finally:
            self._readers.discard(queue)

    async def _call(self) -> None:
        """Place the call, and place it again whenever the camera hangs up."""
        wait = RETRY
        while True:
            started = self._hass.loop.time()
            carried = False
            try:
                carried = await self._once()
            except asyncio.CancelledError:
                raise
            except Exception:
                # One camera's failure must not take the others with it.
                _LOGGER.exception("%s: could not run nooie-proxy", self._name)
            # A call that carried a stream is worth placing again at once. A
            # camera that is off is not, and every attempt is a sign-in.
            lived = self._hass.loop.time() - started
            steady = carried and lived > STEADY
            wait = RETRY if steady else min(wait * 2, MAX_RETRY)
            await asyncio.sleep(wait)

    async def _once(self) -> bool:
        """One call, from the first packet to the last; True if it carried."""
        process = await _spawn(
            self._hass, self._python, self._data, device_id=self._device_id
        )
        self._process = process
        logger = asyncio.create_task(_log(process.stderr))
        carried = False
        try:
            while True:
                self._publish(await process.stdout.readexactly(CHUNK))
                carried = True
        except asyncio.IncompleteReadError:
            pass
        finally:
            self._process = None
            await _close(process)
            said = await logger
        if not carried:
            # Without this the camera is simply never there, and the reason
            # sits in a debug log nobody has turned on.
            _LOGGER.warning("%s did not stream: %s", self._name, said)
        else:
            # The engine's last word says how long the call held and what
            # ended it, which is the whole of what a dropped call leaves.
            _LOGGER.info("%s: %s", self._name, said)
        return carried

    def _publish(self, chunk: bytes) -> None:
        """Hand the chunk to every reader, and never wait for a slow one."""
        for queue in self._readers:
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(chunk)


async def async_serve(
    hass: HomeAssistant,
    entry: ConfigEntry,
    python: str,
    devices: dict[str, Any],
) -> int:
    """Hold a call to each camera, serve them all, and return the port."""
    feeds: dict[str, Feed] = {}
    app = web.Application()
    app.router.add_get("/{device_id}", partial(_handle, feeds))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", 0).start()

    async def async_stop() -> None:
        await runner.cleanup()
        await asyncio.gather(*(feed.async_close() for feed in feeds.values()))

    # Nothing calls a camera until the server that carries it is up, so a
    # server that fails to start leaves no call behind.
    entry.async_on_unload(async_stop)
    # A camera that was off when the account was read cannot answer, and
    # every attempt on it is another sign-in for nothing. Reload the entry to
    # pick one up once it is back.
    asleep = [
        device.get("name", device_id)
        for device_id, device in devices.items()
        if not device.get("online")
    ]
    if asleep:
        _LOGGER.warning(
            "Not calling %s: offline when the account was read. Reload the "
            "integration once the camera is back",
            ", ".join(str(name) for name in asleep),
        )
    feeds.update(
        {
            device_id: Feed(
                hass, python, entry.data, device_id, device.get("name", "")
            )
            for device_id, device in devices.items()
            if device.get("online")
        }
    )
    return int(runner.addresses[0][1])


async def _handle(
    feeds: dict[str, Feed], request: web.Request
) -> web.StreamResponse:
    """Read one camera's feed until the reader goes away."""
    feed = feeds.get(request.match_info["device_id"])
    if feed is None:
        raise web.HTTPNotFound
    response = web.StreamResponse(headers={"Content-Type": "video/mp2t"})
    await response.prepare(request)
    with contextlib.suppress(ConnectionError):
        async with feed.reader() as queue:
            while True:
                await response.write(await queue.get())
    return response

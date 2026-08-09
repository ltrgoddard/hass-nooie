"""Pure helpers: stream naming and URL derivation (no Home Assistant imports)."""

from urllib.parse import urlsplit

from .const import API_STREAMS, RTSP_PORT, STREAM_PREFIX


def is_nooie_stream(name: str) -> bool:
    """Whether a go2rtc stream name belongs to the Nooie add-on."""
    return name.startswith(STREAM_PREFIX)


def friendly_name(stream: str) -> str:
    """Turn 'nooie/living_room' into 'Living Room'."""
    slug = stream.removeprefix(STREAM_PREFIX)
    words = slug.replace("-", " ").replace("_", " ").split()
    return " ".join(word.capitalize() for word in words) if words else stream


def rtsp_url(api_url: str, stream: str) -> str:
    """The RTSP endpoint for a stream on the same host as the go2rtc API."""
    parts = urlsplit(api_url)
    host = parts.hostname or "127.0.0.1"
    return f"rtsp://{host}:{RTSP_PORT}/{stream}"


def api_url(base: str) -> str:
    """Normalise the configured base URL to fetch /api/streams from."""
    return base.rstrip("/") + API_STREAMS

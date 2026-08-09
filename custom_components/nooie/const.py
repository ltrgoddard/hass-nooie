"""Constants for the Nooie integration."""

from datetime import timedelta

DOMAIN = "nooie"
CONF_URL = "url"
# The add-on is reachable by its slug from Home Assistant on OS/Supervised.
# With the add-on's ports mapped to the host instead, use http://127.0.0.1:1984.
DEFAULT_URL = "http://nooie:1984"

# Streams published by the add-on's go2rtc carry this prefix; the integration
# only turns those into camera entities.
STREAM_PREFIX = "nooie/"

# The add-on serves RTSP on this port; the go2rtc HTTP API on 1984.
RTSP_PORT = 8554
API_STREAMS = "/api/streams"

SCAN_INTERVAL = timedelta(seconds=60)

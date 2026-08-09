"""Constants for the Nooie integration."""

from datetime import timedelta

DOMAIN = "nooie"
CONF_URL = "url"
DEFAULT_URL = "http://127.0.0.1:1984"

# Streams published by the add-on's go2rtc carry this prefix; the integration
# only turns those into camera entities.
STREAM_PREFIX = "nooie/"

# The add-on serves RTSP on this port; the go2rtc HTTP API on 1984.
RTSP_PORT = 8554
API_STREAMS = "/api/streams"

SCAN_INTERVAL = timedelta(seconds=60)

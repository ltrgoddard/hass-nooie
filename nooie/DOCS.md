# Nooie

Stream Nooie cameras (WebRTC-only, no RTSP) into Home Assistant. The add-on
places and supervises the WebRTC call per camera and exposes the result as
RTSP via go2rtc.

See [README.md](README.md) for configuration and usage.

## Troubleshooting

- **Camera doesn't appear**: check the add-on log for the device list, then
  make sure the device ID is correct and the camera shows `online`.
- **Stream won't start**: the proxy takes 10–20 seconds to place the call.
  The add-on preloads streams at startup, so give it half a minute before
  opening the camera.
- **Repeated login failures**: the Nooie API throttles abuse. The wrapper
  scripts pause ten seconds between attempts.

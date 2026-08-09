# Nooie

Runs nooie-proxy + go2rtc so your Nooie cameras (WebRTC-only) become RTSP
streams Home Assistant can use.

## Configuration

Set the Nooie `username` and `password` (and `country_code` if your region
isn't `44`). Online cameras are streamed automatically as `nooie/<name>`; the
optional `devices` list selects a subset or renames them. See
[README.md](README.md) for the full picture.

## Troubleshooting

- **No camera appears**: it must be online; the add-on log lists the
  account's cameras at startup.
- **Slow start**: the call takes 10–20 seconds; streams are preloaded at
  add-on startup.
- **Repeated login failures**: the API throttles; the add-on pauses ten
  seconds between attempts.

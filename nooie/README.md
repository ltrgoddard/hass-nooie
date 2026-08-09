# Nooie add-on

Runs [nooie-proxy](../README.md) and [go2rtc](https://github.com/AlexxIT/go2rtc)
so Nooie cameras (WebRTC-only) become RTSP streams Home Assistant and other
tools can consume. One supervised process per camera keeps the call alive;
go2rtc fans the stream out to any number of viewers.

## Configuration

| option | meaning |
| --- | --- |
| `username`, `password` | Nooie account login |
| `country_code` | account region, e.g. `44` |
| `devices` | optional `{ id, name }` pairs; leave empty to stream every online camera |

Each camera is published as `nooie/<name>`, preloaded, at
`rtsp://nooie:8554/nooie/<name>`. With `devices` empty, every camera that is
online is discovered and named after its Nooie app name; the add-on log lists
the account's cameras (the same table `nooie-proxy --list-devices` prints) if
you want to pick a subset or rename.

## Use

- **Home Assistant**: install the `nooie` custom component (HACS or copy
  `custom_components/nooie`), add the integration, and keep the default URL
  (`http://nooie:1984`). Camera entities appear automatically.
- **Anything else**: consume `rtsp://nooie:8554/nooie/<name>` (Frigate, VLC,
  ...); enable the add-on's port mappings to reach it from other machines.

The go2rtc web UI is available via Ingress for debugging.

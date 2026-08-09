# Nooie add-on

Runs [nooie-proxy](../README.md) and [go2rtc](https://github.com/AlexxIT/go2rtc)
so your Nooie cameras appear as RTSP streams that Home Assistant (and Frigate,
VLC, or anything else) can consume. One wrapper script per camera keeps the
WebRTC call alive; go2rtc fans the MPEG-TS out to any number of viewers.

## Configuration

The add-on needs your Nooie account:

| option | meaning |
| --- | --- |
| `username` | the account email |
| `password` | the account password |
| `country_code` | account region, e.g. `44` |
| `devices` | optional: `{ id, name }` pairs to stream only some cameras, or rename them |

With just the credentials set, every camera that is online is discovered and
streamed automatically, named after its Nooie app name. Leave `devices` empty
for that; to pick a subset (or name streams yourself), add `{ id, name }`
entries — the add-on logs every camera on the account (`uuid`, name, model,
online) at startup, or run `nooie-proxy --list-devices`.

## Using it

The add-on publishes one stream per camera named `nooie/<name>` (e.g.
`nooie/living_room`), preloaded so the call is already connected when you open
the camera.

- **In Home Assistant**: install the companion `nooie` custom component
  (HACS or `custom_components/nooie`), add it, and point it at
  `http://nooie:1984` (HA OS/Supervised) or `http://127.0.0.1:1984` (HA
  Container with the ports mapped). Camera entities appear automatically.
- **Manually**: add a Generic Camera with
  `stream_source: rtsp://nooie:8554/nooie/<name>`.
- **Frigate/other NVRs**: point them at the same RTSP URL (map port `8554`
  if they run outside the Home Assistant host).

Ports `1984`, `8554`, and `8555` are exposed to the host only if you enable
them in the add-on settings. The go2rtc web UI is available from the sidebar
(Ingress) for debugging.

## Building the image yourself

The Dockerfile installs nooie-proxy from GitHub at a pinned commit, so the
repository needs to be public (or the package published to PyPI, in which case
build with `--build-arg NOOIE_PKG="nooie-proxy==0.3.0"`). When a new
nooie-proxy release is wanted, bump the pinned SHA here and the add-on version
in `config.yaml`.

# Nooie for Home Assistant

Brings your Nooie cameras (WebRTC-only, no official app) into Home Assistant
as live camera entities, without decoding or re-encoding the stream. An
add-on runs the bundled nooie-proxy engine and
[go2rtc](https://github.com/AlexxIT/go2rtc) to turn each camera's WebRTC
stream into RTSP, WebRTC, and HLS; a custom component turns those into camera
entities.

## Quick start

1. **Add-on** — in Home Assistant, go to *Settings → Add-ons → Add-on store
   → ⋯ → Repositories*, add `https://github.com/ltrgoddard/hass-nooie`,
   install the **Nooie** add-on, and enter your Nooie account `username`,
   `password`, and `country_code`. Every online camera is discovered
   automatically and streamed as `nooie/<name>`.
2. **Component** — install the `nooie` integration (HACS → ⋯ → *Custom
   repositories* → add `https://github.com/ltrgoddard/hass-nooie` as an
   *Integration*, or copy `custom_components/nooie` into `config/`), add it,
   and keep the default URL (`http://nooie:1984`). Camera entities appear
   automatically.

See [nooie/README.md](nooie/README.md) for the full add-on picture
(including how to pick a subset of cameras or rename them), and
[nooie/DOCS.md](nooie/DOCS.md) for troubleshooting.

## What's in this repository

| path | |
| --- | --- |
| `nooie/` | the Home Assistant add-on (README, docs, Dockerfile) |
| `custom_components/nooie/` | the camera integration |
| `proxy/` | the bundled nooie-proxy CLI — a standalone package with its own [README](proxy/README.md) |

The add-on supervises one nooie-proxy process per camera and preloads every
stream; go2rtc fans each one out to any number of viewers at
`rtsp://nooie:8554/nooie/<name>` (the go2rtc web UI is available via
Ingress). The proxy muxes the camera's own H.264/AAC straight to MPEG-TS —
nothing is decoded or re-encoded, so it costs a few percent of one core.

Want the raw CLI without Home Assistant? Head to
[proxy/README.md](proxy/README.md).

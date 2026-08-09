# Nooie for Home Assistant

Nooie cameras use WebRTC and have no RTSP output. This repository
makes them available in Home Assistant as camera entities. An add-on runs the
[nooie-proxy](https://github.com/ltrgoddard/nooie-proxy) engine and
[go2rtc](https://github.com/AlexxIT/go2rtc), which convert each WebRTC stream
into RTSP, WebRTC, and HLS. A custom component turns those streams into
entities.

The proxy copies the camera's H.264 and AAC into MPEG-TS as the media
arrives. It does not decode or re-encode the media, so a camera costs a few
percent of one core.

## Quick start

1. In Home Assistant, go to Settings → Add-ons → Add-on store → ⋯ →
   Repositories. Add `https://github.com/ltrgoddard/hass-nooie`.
2. Install the Nooie add-on. Enter your Nooie account `username` and
   `password`, and your mobile phone's `country_code`. The add-on finds every
   online camera and streams it as `nooie/<name>`.
3. Install the `nooie` integration. In HACS, go to ⋯ → Custom repositories.
   Add `https://github.com/ltrgoddard/hass-nooie` as an Integration. You can
   also copy `custom_components/nooie` into `config/`.
4. Add the integration. Keep the default URL, `http://nooie:1984`. The camera
   entities appear automatically.

## Contents

| path | contents |
| --- | --- |
| `nooie/` | the Home Assistant add-on |
| `custom_components/nooie/` | the camera integration |

The add-on runs one nooie-proxy process for each camera and preloads every
stream. go2rtc then serves each stream to every viewer that connects to
`rtsp://nooie:8554/nooie/<name>`. The go2rtc web interface is available
through Ingress.

To use the proxy without Home Assistant, see
[nooie-proxy](https://github.com/ltrgoddard/nooie-proxy). The add-on installs
it from PyPI at the version pinned in [nooie/Dockerfile](nooie/Dockerfile).

For the add-on options, see [nooie/README.md](nooie/README.md). For
troubleshooting, see [nooie/DOCS.md](nooie/DOCS.md).

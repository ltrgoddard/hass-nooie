# Nooie for Home Assistant

Nooie cameras use WebRTC and have no RTSP output. This integration makes them
available in Home Assistant as camera entities. It runs the
[nooie-proxy](https://github.com/ltrgoddard/nooie-proxy) engine, which places
the WebRTC call and copies the camera's H.264 and AAC into MPEG-TS. It does
not decode or re-encode the media, so a camera costs a few percent of one
core.

Home Assistant already runs go2rtc, so the integration does not ship one, and
there is no add-on and no container. The integration works on Home Assistant
OS, Supervised, Container, and Core. Install it, sign in, and the cameras
appear.

## Quick start

1. In HACS, go to ⋯ → Custom repositories. Add
   `https://github.com/ltrgoddard/hass-nooie` as an Integration. You can also
   copy `custom_components/nooie` into `config/`.
2. Restart Home Assistant, then add the Nooie integration.
3. Enter your Nooie account username and password, and your mobile phone's
   country code. Every camera on the account becomes a camera entity.

Each camera holds one call open for as long as the integration is loaded, so
the live view starts at once. To pick up a camera you have added to the
account, reload the integration.

## How it works

The integration runs one `nooie-proxy` process for each camera and serves the
result on a loopback port, one path for each camera. A camera entity reports a
stream source of `http://127.0.0.1:<port>/<uuid>`. go2rtc reads that and
serves the live view, the snapshots, and anything else that asks.

Three things fix that shape:

- Home Assistant lets go2rtc execute the ffmpeg binary and nothing else, so
  go2rtc cannot start the proxy. It has to be given a URL that it can read,
  and HTTP is the one that the stream component reads as well.
- go2rtc gives a new source five seconds to declare its tracks, and a Nooie
  call takes 10 to 20 seconds to answer. The call is therefore held open, and
  a reader joins the stream that is already running.
- One camera, one call: the proxy signs in, registers one NAT mapping, and
  places one call for each process. The integration hands the stream to as
  many readers as ask for it.

The proxy is installed from PyPI at the version pinned in
[manifest.json](custom_components/nooie/manifest.json). It keeps the UUID that
names this install in `config/nooie-proxy/`. Do not edit or delete that file.
Your password is held in the config entry and given to each proxy process in
its environment. It is not written to disk anywhere else.

To use the proxy on its own, see
[nooie-proxy](https://github.com/ltrgoddard/nooie-proxy).

## Troubleshooting

- **No camera appears**: the account must have at least one camera. The
  integration reports what nooie-proxy said when a sign-in fails.
- **A camera shows no picture**: the camera is probably offline. The
  integration places the call again every minute.
- **The picture breaks up when it starts**: a reader joins between keyframes
  and synchronizes at the next one, which takes about two seconds.
- **Something else is wrong**: turn on debug logging for
  `custom_components.nooie`. Every line the proxy prints appears there.

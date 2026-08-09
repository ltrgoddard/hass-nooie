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

The first sign-in takes a minute or two, while the integration builds the
engine's environment. Later ones are immediate.

Each camera holds one call open for as long as the integration is loaded, so
the live view starts at once. To pick up a camera you have added to the
account, reload the integration.

## How it works

The integration runs one `nooie-proxy` process for each camera and serves the
result on a loopback port, one path for each camera. A camera entity reports a
stream source of `http://127.0.0.1:<port>/<uuid>`. go2rtc reads that and
serves the live view, the snapshots, and anything else that asks.

Four things fix that shape:

- Home Assistant lets go2rtc execute the ffmpeg binary and nothing else, so
  go2rtc cannot start the proxy. It has to be given a URL that it can read,
  and HTTP is the one that the stream component reads as well.
- go2rtc gives a new source five seconds to declare its tracks, and a Nooie
  call takes 10 to 20 seconds to answer. The call is therefore held open, and
  a reader joins the stream that is already running.
- One camera, one call: the proxy registers one NAT mapping and places one
  call for each process. The integration hands the result to as many readers
  as ask for it.
- Nooie's account layer holds one session for each install, so each camera
  signs in as an install of its own. Cameras that share one sign each other
  out, and then none of them streams.

## What it writes

Everything lives under `config/nooie/`.

| path | contents |
| --- | --- |
| `venv/` | the engine and its dependencies |
| `<uuid>/` | one camera's install identity |

The engine is not a Home Assistant requirement, because it is a program
rather than a library. Home Assistant pins the versions that an integration's
requirements resolve against, PyAV among them, and the engine needs a newer
PyAV than the pin. Its own environment settles that at this release and at
every later one. It costs about half the disk of the container this
integration replaced. To move to a new engine, change `VERSION` in
[proxy.py](custom_components/nooie/proxy.py) and reload.

Do not edit or delete the identity files. Your password is held in the config
entry and given to each process in its environment. It is not written to disk
anywhere else.

To use the engine on its own, see
[nooie-proxy](https://github.com/ltrgoddard/nooie-proxy).

## Troubleshooting

- **No camera appears**: the account must have at least one camera. The
  integration reports what the engine said when a sign-in fails.
- **A camera shows no picture**: the log names the camera and the reason. An
  offline camera is the usual one. The call is placed again on a wait that
  doubles up to ten minutes, because every attempt is a sign-in and Nooie
  limits the rate of those.
- **A camera streams for a few seconds and stops, again and again**: a Nooie
  camera answers one call at a time. Something else is holding it: the Nooie
  app, or nooie-proxy run by hand. Close that, and the call holds. This is
  why the integration places one call for each camera and shares it, rather
  than placing one for each viewer.
- **The picture breaks up when it starts**: a reader joins between keyframes
  and synchronizes at the next one, which takes about two seconds.
- **Something else is wrong**: turn on debug logging for
  `custom_components.nooie`. Every line the engine prints appears there.

# next step

## what is settled

| finding | how it was established |
| --- | --- |
| the integration must hand go2rtc a URL it can pull | Home Assistant's managed go2rtc sets `exec: allow_paths: [ffmpeg]` |
| HTTP MPEG-TS is that URL | go2rtc pulled the loopback source, read `video H264` and `audio MPEG4-GENERIC/16000/1`, and returned a 2304x1296 frame |
| calls must be held open, and readers handed whole packets | go2rtc allows a source five seconds to declare its tracks, and its sniffer wants `0x47` in the first byte |
| the engine needs an environment of its own | Home Assistant pins PyAV 16; the engine calls `add_mux_stream`, which is PyAV 17. the private environment builds in seconds and takes 87 MB |
| an account session is scarce | one identity for every camera gives `USER_SESSION_INVALID`; one for each camera gives `USER_SESSION_LIMIT` |
| a call ends 8 to 18 seconds after it connects | reproduced outside Home Assistant, to UDP and to stdout, on two identities. cause unknown |
| a call can hold much longer than that | earlier the same evening one call ran past a minute and served two readers at once |

the two identity strategies are not a bug and its fix. they are the same
shortage seen from two sides, and the choice between them only picks the
error message.

## what is not known

| # | question |
| --- | --- |
| U1 | does one call hold, when nothing else touches the account? |
| U2 | can the account carry two calls at once, on two cameras? |
| U3 | what spends a session, how many are allowed, and how fast does one clear? |
| U4 | can one process carry two calls, on one signalling websocket and one NAT mapping? |

U2 and U4 decide the architecture. answer them before you build anything.

## experiments

the account is at its session limit, so leave it alone for some hours
first. then make sure that nothing else calls a camera:

- make `launchctl print gui/$(id -u)/eco.datadesk.nooie-proxy` fail.
- close the Nooie app.
- stop Home Assistant.

keep every log.

- **E1 (U1)** attach a reader. run one camera to `udp://127.0.0.1:5004` for
  ten minutes. when the tracks end, record the time. run it a second time.
  a call that holds makes the short calls contention. a call that does not
  hold puts the fault in the call itself, and the rest of this plan waits
  on it.
- **E2 (U3)** sign in repeatedly with `--list-devices` and no streaming.
  find where the limit falls and how long it takes to clear. this sets the
  retry budget, which is guesswork today.
- **E3 (U2)** two processes, two online cameras, separate identities. does
  either hold?
- **E4 (U4)** one process, two calls, sharing the signalling websocket and
  one apeman registration. a throwaway script, not a feature.

## what the answers decide

| outcome | shape |
| --- | --- |
| E1 fails | fix the call first. nothing else matters |
| E3 holds | one process for each camera stands. keep the per-camera identity and spend the effort on session thrift |
| E3 fails, E4 holds | one process, one session, many calls. build `--serve` in nooie-proxy; hass-nooie shrinks to starting it and reading its port |
| E3 and E4 both fail | one camera at a time. the integration must then call on demand and hand the account between cameras, and say so plainly |

## nooie-proxy

1. **correct the PyAV floor.** the package declares `av>=15,<18` and calls
   `add_mux_stream`, which is not in 16. find the version that added it and
   raise the floor to it. as it stands the metadata promises something the
   code does not deliver, which is how this reached a running Home Assistant.
2. **spend fewer sessions.** every run signs in to Nooie and to Thing from
   nothing, and every retry does it again. cache the api-token and the Thing
   session beside the identity, with their expiry, and reuse them. this is
   worth doing whatever the answers are, and it can be what makes E3 pass.
3. **`--serve HOST:PORT`, only if E4 holds.** one sign-in, one presence, one
   registration, a call for each camera, MPEG-TS at `/<uuid>` and the camera
   list at `/`. this evening's attempt is not in the repository. it needs a
   shared signalling channel, which `matching_signal` has the pieces for, and
   a shared NAT mapping, which it does not.
4. **one line when a call ends.** the last line of a traceback is the least
   useful part of it, and the integration shows exactly that line.

## hass-nooie

1. **revisit the per-camera identity** from `74cc9f4` after E2 answers U3.
   one session for the account is the likelier right answer.
2. **do not call cameras that were offline at setup.** they cannot stream,
   and their retries spend sessions that the working cameras need.
3. **make sure that the still image works on a Docker Home Assistant.** a
   direct request to go2rtc returned a frame, but Home Assistant fell back to
   the stream component and answered 500. Home Assistant manages go2rtc only
   in Docker, through `is_docker_env()`, so a venv install cannot settle
   this.
4. **pin the engine again** through `VERSION` in `proxy.py`, once the next
   nooie-proxy release is on PyPI.

## the test rig

`/tmp/ha-nooie` is throwaway, and the way to it was not obvious. a local
Home Assistant with this integration needs:

- a seeded venv and `homeassistant`.
- the go2rtc binary on PATH, because Home Assistant starts one only in
  Docker.
- a symlink into `custom_components`.
- onboarding through `/api/onboarding`.
- a `logger:` block for `custom_components.nooie`.

keep that as a project skill rather than find it again.

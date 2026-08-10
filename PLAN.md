# next step

## what constrains the design

| finding | how it was established |
| --- | --- |
| Nooie's signalling holds one websocket for each install, and a second connection closes the first | a second process on the same identity closed the first one's websocket a second after connecting, before it had placed its call. the call it was carrying ended at once |
| a second install does not disturb the first | a websocket opened under a fresh identity and held. the call already running streamed through it and past it |
| the camera answers a call with no Tuya presence at all | the proxy placed and held calls with `thing.presence` skipped, one of them for 593 seconds, ended by its own timeout rather than by the camera |
| a camera that has been idle overnight answers without the Tuya presence | the first call of 2026-08-10, placed with nothing else on the account after 10.6 hours idle, answered in 9 seconds and streamed steadily until it was stopped by hand at 135 seconds |
| the still image works on a container Home Assistant with a managed go2rtc | an official-image Home Assistant under Apple's `container` runtime started its own go2rtc 1.9.14 (the official image alone satisfies `is_docker_env()`), the engine's venv built from musllinux wheels in 8 seconds, and `camera_proxy` returned a live frame |
| a fresh Nooie login is refused with code 1053, while stored sessions keep working | on 2026-08-10 the same fresh login failed identically from the host and the container, minutes after a cached session had streamed for 135 seconds; a transplanted session then called and streamed again |
| the Tuya account layer was the whole of the session shortage | every `USER_SESSION_LIMIT` and `USER_SESSION_INVALID` came from `smartlife.m.user.uid.password.login` or `m.life.home.space.list`. Nooie's own API answered throughout, and a refused Tuya session does not clear for at least half an hour |
| `add_mux_stream` is PyAV 17.0.0 | the changelog says so, and `OutputContainer` has no such attribute in 16.1.0. Home Assistant pins 16 |
| a reader that joins a call in progress synchronizes in seconds | ffmpeg attached two minutes into a call and read 13 fps for the rest of it |

One install, one websocket, is why each camera keeps an install of its own,
and why `--serve`, one process carrying every camera, is not worth building:
it would put every call on one install, which is the one arrangement that
does not work.

The calls that ended after 8 to 18 seconds fit the Tuya layer and nothing
else that was measured. Two cameras meant two Tuya logins, a login replaces
the account's session, and the drops stopped when the layer did. Their two
installs cannot have closed each other's websockets, because a second install
does not do that.

## what is not known

| # | question |
| --- | --- |
| U1 | can two cameras stream at once? |
| U3 | does the login refusal (code 1053) clear, and on what timescale? |

U1 is expected to work, because installs do not disturb each other, but it
has not been seen: the second camera has been offline, so every result here
is one camera. Bring it up and watch both hold.

U3 appeared on 2026-08-10 and fits the 0.1.0 era, when every call attempt
was a fresh login: the account has likely tripped a rate or device control.
The engine caches its session since 0.2.0, so a working install never logs
in again, but a new install cannot be created until 1053 clears. If it
never clears, the fix is to stop registering fresh installs: seed new
installs from a stored session, as the container was seeded.

U2, whether a camera idle overnight answers without the Tuya presence, was
the one that could have undone the deletion. It is now a finding: the first
call of the morning answered like any other, so the deletion stands and
there is nothing to cache.

## next

1. **Answer U3 with one fresh `--list-devices` from the host**, no earlier
   than tomorrow. Do not attempt any other login until then.
2. **Bring the second camera online and answer U1.** The container Home
   Assistant reads the account with its cached session, so a reload costs
   no login.

The container Home Assistant at `/tmp/ha-docker` holds copies of the rig's
installs, account and camera alike. One websocket for each install: run the
container and the rig one at a time.

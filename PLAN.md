# next step

## what constrains the design

| finding | how it was established |
| --- | --- |
| Nooie's signalling holds one websocket for each install, and a second connection closes the first | a second process on the same identity closed the first one's websocket a second after connecting, before it had placed its call. the call it was carrying ended at once |
| a second install does not disturb the first | a websocket opened under a fresh identity and held. the call already running streamed through it and past it |
| the camera answers a call with no Tuya presence at all | the proxy placed and held calls with `thing.presence` skipped, one of them for 593 seconds, ended by its own timeout rather than by the camera |
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
| U2 | does a camera that has been idle overnight answer without the Tuya presence? |

U1 is expected to work, because installs do not disturb each other, but it
has not been seen: the second camera has been offline, so every result here
is one camera. Bring it up and watch both hold.

U2 is the one that could undo this. The presence cannot plausibly wake a
camera, because nothing was ever published on it, but the only proof is the
first call of a morning with nothing else running. If that call fails and the
presence fixes it, revert the deletion and cache the Tuya session instead:
`cache.py` takes a second entry without changing.

## next

1. **Answer U2 in the morning**, before anything else touches the account.
   Stop the rig first: it holds a call open for as long as it runs.
2. **Make sure the still image works on a Docker Home Assistant.** It works
   on the rig, but Home Assistant manages go2rtc only in Docker, through
   `is_docker_env()`, and a managed go2rtc is not the rig's.
3. **Bring the second camera online and answer U1.**

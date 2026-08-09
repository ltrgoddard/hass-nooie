# next step

## what the evening established

| finding | how it was established |
| --- | --- |
| every session error came from Tuya, not Nooie | each `USER_SESSION_LIMIT` and `USER_SESSION_INVALID` in the logs was raised by `smartlife.m.user.uid.password.login` or `m.life.home.space.list`. Nooie's own API answered `--list-devices` all evening, including while Tuya refused |
| the camera answers a call with no Tuya presence at all | the proxy placed a call with `thing.presence` skipped, while Tuya was still refusing the login |
| a call holds | with the Tuya layer skipped and nothing else running: 593 s of streaming, ended by the ten-minute timeout rather than by the camera. a reader took 5779 frames |
| Nooie's signalling holds one websocket for each install | a second process, on the same identity, closed the first one's websocket one second after it connected and before it had placed its call. the first call ended with 121 s streamed; the second then ran to its own timeout |
| a second install does not disturb the first | a websocket opened under a fresh identity and held for 40 s. the call already running streamed through it and past it, to 172 s |
| the Tuya limit does not clear quickly | refused again at 21:57 and 22:02, half an hour after the last login that took a session |
| `add_mux_stream` is PyAV 17.0.0 | the changelog says so, and `OutputContainer` has no such attribute in 16.1.0. Home Assistant pins 16, which is the `AttributeError` in last night's log |
| a reader that joins a call in progress synchronizes in seconds | ffmpeg attached two minutes in, complained about a missing PPS eight times, and then read 13 fps for the rest of the call |
| the integration works end to end | a Home Assistant built from nothing signed in, skipped the offline camera, called the other, and streamed 8 seconds after setup. `/api/camera_proxy` returned a 2304x1296 frame, where last night it answered 500 |

The 8 to 18 second calls fit the Tuya layer and nothing else that was
measured. Two cameras meant two Tuya logins, a login replaces the account's
session, and the drops stopped as soon as the layer did. Their two installs
cannot have closed each other's websockets, because a second install does not
do that. This is the explanation that fits rather than one that was watched
happening, and the logs it would have been watched in are gone.

Either way the layer is deleted. What it cost was real, and what it bought
was a subscription to a mailbox nothing ever published to.

One install, one websocket, is why each camera keeps an install of its own.
That was already the shape, for the wrong reason.

## what is still not known

| # | question |
| --- | --- |
| U2 | can two cameras stream at once? |
| U5 | does a camera that has been idle overnight answer without the Tuya presence? |

U2 is now expected to work, because installs do not disturb each other, but
it has not been seen: Spyguy has been offline all evening, so every result
here is one camera. Bring a second camera up and watch both hold.

U5 is the one that could undo this. The presence cannot plausibly wake a
camera, because nothing was ever published on it, but the only proof is the
first call of a morning with nothing else running. If that call fails and the
presence fixes it, revert the deletion and cache the Tuya session instead:
`cache.py` takes a second entry without changing.

`--serve`, one process carrying every camera, is off the table. It would put
every call on one install, which is the one arrangement that does not work.

## next

1. **Tag `nooie-proxy` v0.2.0, which is the one thing standing in the way.**
   The tag is what publishes it. `VERSION` in
   [proxy.py](custom_components/nooie/proxy.py) already asks for `0.2.0`,
   because `0.1.0` cannot stream at all, and a version that is not on PyPI
   fails at the install with a plain message rather than at the call with a
   puzzling one. Tonight's end-to-end run used the checkout in its place.
2. **Answer U5 in the morning**, before anything else touches the account.
3. **Make sure the still image works on a Docker Home Assistant.** It works
   on the rig now, but Home Assistant manages go2rtc only in Docker, through
   `is_docker_env()`, and a managed go2rtc is not this one. Docker is
   installed on this machine.
4. **Bring Spyguy online and answer U2.**

## what was done

`nooie-proxy`:

- the Tuya account layer is gone: `thing.py`, its tests, its half of
  `profile.py`, and the `aiomqtt` dependency.
- `cache.py` keeps the Nooie session beside the identity and reuses it, so a
  restart and a retry are not each a sign-in. A stored session that is
  refused is thrown away and signed in for again, which is what an expiry
  field would have bought, had either service offered one.
- the PyAV floor is 17, where `add_mux_stream` begins.
- a call ends on one line saying how long it held and what ended it. That
  line is how the websocket eviction was found.

`hass-nooie`:

- cameras that were offline when the account was read are not called, their
  entities say unavailable, and the log names them.
- the engine's last line is logged when a call drops, not only when a call
  never starts.
- the engine is pinned to `0.2.0`.
- the throwaway Home Assistant is a project skill, with the go2rtc config and
  the onboarding it needs. It builds from nothing in about two minutes.

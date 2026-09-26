# next step

## what constrains the design

| finding | how it was established |
| --- | --- |
| Nooie's signalling holds one websocket for each install, and a second connection closes the first | a second process on the same identity closed the first one's websocket a second after connecting, before it had placed its call. the call it was carrying ended at once |
| a second install does not disturb the first | a websocket opened under a fresh identity and held. the call already running streamed through it and past it |
| the camera answers a call with no Tuya presence at all | the proxy placed and held calls with `thing.presence` skipped, one of them for 593 seconds, ended by its own timeout rather than by the camera |
| a camera that has been idle overnight answers without the Tuya presence | the first call of 2026-08-10, placed with nothing else on the account after 10.6 hours idle, answered in 9 seconds and streamed steadily until it was stopped by hand at 135 seconds |
| the still image works on a container Home Assistant with a managed go2rtc | an official-image Home Assistant under Apple's `container` runtime started its own go2rtc 1.9.14 (the official image alone satisfies `is_docker_env()`), the engine's venv built from musllinux wheels in 8 seconds, and `camera_proxy` returned a live frame |
| code 1053 is a wrong password, not a block | a wrong password on the real account returns 1053 with `residue_degree` 4, the attempts left before a lockout; an unknown account returns 1055. On 2026-09-26 the refusals came from sourcing `.env` in the shell, which expands the quoted password's special characters. The proxy's literal parse signed in at once |
| a fresh sign-in ends every other session on the account | on 2026-09-26 install A signed in, install B signed in, and A's stored session was then refused. The phone app is one more session, which fits the US report of post 24 |
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
| U4 | does a US account sign in on `app.us.nooie.com`? |

U1 is expected to work, because installs do not disturb each other, but it
has not been seen: the second camera has been offline, so every result here
is one camera. Bring it up and watch both hold.

U2, whether a camera idle overnight answers without the Tuya presence, was
the one that could have undone the deletion. It is now a finding: the first
call of the morning answered like any other, so the deletion stands and
there is nothing to cache.

U4 comes from the forum (thread 189977, post 21): a US user with a good
login was rejected at every country code. nooie-proxy 0.2.0 hard-codes the
EU hosts, and `app.us`, `wss.us` and `policy-us` all resolve, so the account
is almost certainly held in the other region. nooie-proxy 0.2.1 asks `global.nooie.com/v2/account/country`, as the app does, and
uses the hosts it names: `us`, `eu` or `cn`. Anything it does not know,
`001` and `US` included, gets `us`. The lookup follows the account, not the
country: this EU account comes back `eu`, `exist` 1, at country 1, 44 and
86 alike, so the country code stops mattering for an account that exists.
On 2026-09-20 the new path did one fresh sign-in (lookup, login, device
list), reused a session stored before it, and streamed 30 s, all on `eu`.
No US account is to hand, so only the reporter can confirm `us`.

The integration signs in twice per load (`account/` and `<uuid>/`), so it
evicts itself as well as the phone app. The fix is one session shared by
every install. A copy of A's session streamed from a new identity without
signing in, but A's session was refused afterwards, and that call and a
control call from A alone both ended after 9 s and 36 s with "the camera
stopped sending audio". Whether a session survives use under a second
identity is not settled.

## next

0. **Ask the forum reporter to try a second Nooie account** with the camera
   shared to it, and for the debug log of `custom_components.nooie`. A
   stream that holds on the shared account confirms the eviction for them.

1. **Never source `.env` in the shell.** Run the proxy from the checkout,
   or let `onboard.py` read it: both take the value literally. A wrong
   password costs one of the few attempts before a lockout.
2. **Bring the second camera online and answer U1.** The container Home
   Assistant reads the account with its cached session, so a reload costs
   no login.

The container Home Assistant at `/tmp/ha-docker` holds copies of the rig's
installs, account and camera alike. One websocket for each install: run the
container and the rig one at a time.

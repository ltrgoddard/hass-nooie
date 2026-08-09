---
name: home-assistant-rig
description: Stand up a throwaway Home Assistant that loads this integration, sign it in, and watch what it does. Use this to try a change to custom_components/nooie against a real Home Assistant, to read the integration's debug log, or to check what go2rtc makes of the stream.
---

# a throwaway home assistant

`rig.sh` builds one under `/tmp/ha-nooie` and starts it. `onboard.py` walks
the onboarding and adds the integration. neither asks anything.

```sh
.claude/skills/home-assistant-rig/rig.sh          # build and start
.claude/skills/home-assistant-rig/onboard.py      # onboard and add nooie
tail -f /tmp/ha-nooie/ha.log                      # what the integration says
pkill -f 'ha-nooie/venv/bin'                      # stop both
```

the rig is disposable. `rm -rf /tmp/ha-nooie` and run `rig.sh` again to start
from nothing. it costs a sign-in, and the account has few to spare.

## what the rig needs, and why

- **a venv with `homeassistant` in it.** the integration is loaded from a
  symlink at `config/custom_components/nooie`, so an edit in the checkout is
  live at the next restart.
- **the go2rtc binary on PATH.** home assistant starts a go2rtc of its own
  only in docker, through `is_docker_env()`. everywhere else it expects one
  already running and reads `go2rtc: url:` to find it. `rig.sh` fetches the
  binary and starts it on `127.0.0.1:1984`.
- **`go2rtc.yaml` as home assistant writes it.** the copy here mirrors the
  managed one, `exec: allow_paths: [ffmpeg]` included. that line is why the
  integration serves HTTP rather than letting go2rtc run the engine, so a
  rig without it proves nothing.
- **onboarding.** a fresh install answers 404 on everything until a user
  exists. `onboard.py` posts through `/api/onboarding`, then starts the
  config flow with the credentials in the checkout's `.env`.
- **a `logger:` block.** `custom_components.nooie` at debug puts every line
  the engine prints into `ha.log`.

## reading it

| file | contents |
| --- | --- |
| `/tmp/ha-nooie/ha.log` | home assistant, the integration, and the engine |
| `/tmp/ha-nooie/go2rtc.log` | what go2rtc made of the stream |
| `/tmp/ha-nooie/token` | a long-lived token for the REST API |

to ask go2rtc for a frame, which skips home assistant's stream component:

```sh
curl -s -o /tmp/frame.jpg \
  'http://127.0.0.1:1984/api/frame.jpeg?src=camera.<name>'
```

to ask home assistant for the same thing, which does not:

```sh
curl -s -H "Authorization: Bearer $(cat /tmp/ha-nooie/token)" \
  -o /tmp/frame.jpg http://127.0.0.1:8123/api/camera_proxy/camera.<name>
```

## what the rig cannot settle

home assistant manages go2rtc only under docker. a still image that fails
there and works here is the difference between a managed go2rtc and this
one, and only a container can tell them apart.

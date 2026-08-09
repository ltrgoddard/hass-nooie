# Nooie add-on

The add-on runs [nooie-proxy](https://github.com/ltrgoddard/nooie-proxy) and
[go2rtc](https://github.com/AlexxIT/go2rtc), which turn Nooie cameras into
RTSP streams that Home Assistant and other tools can read. One supervised
process for each camera keeps the call open. go2rtc serves each stream to
every viewer that connects.

## Options

| option | meaning |
| --- | --- |
| `username`, `password` | the Nooie account login |
| `country_code` | your mobile phone's country code, for example `44` |
| `devices` | optional `{ id, name }` pairs. Leave this empty to stream every online camera |

The add-on preloads each camera and publishes it as `nooie/<name>` at
`rtsp://nooie:8554/nooie/<name>`. When `devices` is empty, the add-on finds
every online camera and names it after the camera's name in the Nooie app. At
startup the add-on log lists the cameras on the account, which is the table
that `nooie-proxy --list-devices` prints. Use that list to select a subset of
the cameras, or to rename one.

## Use

- **Home Assistant**: install the `nooie` custom component through HACS, or
  copy `custom_components/nooie`. Add the integration. Keep the default URL,
  `http://nooie:1984`. The camera entities appear automatically.
- **Other tools**: read `rtsp://nooie:8554/nooie/<name>` from Frigate, VLC,
  or a similar tool. To reach that address from a different machine, enable
  the port mappings of the add-on.

The go2rtc web interface is available through Ingress for debugging.

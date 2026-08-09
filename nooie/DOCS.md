# Nooie

The add-on runs nooie-proxy and go2rtc, which turn your Nooie cameras into
RTSP streams that Home Assistant can read.

## Configuration

Set the Nooie `username` and `password`. If your region is not `44`, set
`country_code`. The add-on streams every online camera as `nooie/<name>`. To
select a subset of the cameras, or to rename one, use the optional `devices`
list. For more information, see [README.md](README.md).

## Troubleshooting

- **No camera appears**: the camera must be online. At startup the add-on log
  lists the cameras on the account.
- **The stream starts slowly**: each call takes 10 to 20 seconds. The add-on
  preloads the streams at startup.
- **Login fails repeatedly**: the Nooie API limits the login rate. The add-on
  waits ten seconds between attempts.

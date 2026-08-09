#!/usr/bin/env python3
"""Turn /data/options.json into go2rtc config and per-camera wrappers,
then hand over to go2rtc (which supervises the proxy processes).
"""

import json
import os
import pathlib
import shlex
import sys

GO2RTC = os.environ.get("NOOIE_GO2RTC", "/usr/local/bin/go2rtc")
CONFIG = os.environ.get("NOOIE_CONFIG", "/data/go2rtc.yaml")
WRAP_DIR = pathlib.Path(os.environ.get("NOOIE_WRAP_DIR", "/data/cameras"))
OPTIONS = os.environ.get("NOOIE_OPTIONS", "/data/options.json")
PORT_API = 1984
PORT_RTSP = 8554
PORT_WEBRTC = 8555


def slugify(name: str) -> str:
    words = "".join(c if c.isalnum() else " " for c in name.lower()).split()
    return "_".join(words) if words else "camera"


def wrapper(
    device_id: str, username: str, password: str, country: str
) -> str:
    """A shell loop: run the proxy, and pick it up when the camera hangs up."""
    lines = [
        "#!/bin/sh",
        "export XDG_CONFIG_HOME=/data",
        f"export NOOIE_USERNAME={shlex.quote(username)}",
        f"export NOOIE_PASSWORD={shlex.quote(password)}",
        f"export NOOIE_COUNTRY_CODE={shlex.quote(country)}",
        f"export NOOIE_DEVICE_ID={shlex.quote(device_id)}",
        "trap 'trap - TERM; kill -TERM $pid 2>/dev/null; exit 0' TERM INT",
        "while :; do",
        "  nooie-proxy &",
        "  pid=$!",
        "  wait $pid",
        "  sleep 10 &",
        "  wait $!",
        "done",
    ]
    return "\n".join(lines) + "\n"


def list_devices(username: str, password: str, country: str) -> None:
    """Log every camera on the account so the user can fill in devices."""
    import subprocess

    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = "/data"
    env["NOOIE_USERNAME"] = username
    env["NOOIE_PASSWORD"] = password
    env["NOOIE_COUNTRY_CODE"] = country
    try:
        result = subprocess.run(
            ["nooie-proxy", "--list-devices"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
    except Exception as error:
        print(f"nooie: could not list devices: {error}", file=sys.stderr)
        return
    print(result.stdout or result.stderr, file=sys.stderr, end="")


def main() -> None:
    options = json.load(open(OPTIONS))
    username = str(options.get("username", ""))
    password = str(options.get("password", ""))
    country = str(options.get("country_code", "44"))
    devices = [
        device
        for device in (options.get("devices") or [])
        if isinstance(device, dict) and str(device.get("id", "")).strip()
    ]

    if not username or not password:
        print(
            "nooie: username/password not configured yet; "
            "set them in the add-on options",
            file=sys.stderr,
        )
    else:
        list_devices(username, password, country)

    if not devices:
        print(
            "nooie: no cameras configured yet; "
            "pick device IDs from the list above",
            file=sys.stderr,
        )

    WRAP_DIR.mkdir(parents=True, exist_ok=True)
    streams: list[str] = []
    preload: list[str] = []
    used: set[str] = set()
    for device in devices:
        device_id = str(device.get("id", "")).strip()
        base = slugify(str(device.get("name", "")))
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}_{n}"
            n += 1
        used.add(slug)
        script = WRAP_DIR / f"{slug}.sh"
        script.write_text(wrapper(device_id, username, password, country))
        script.chmod(0o755)
        stream = f"nooie/{slug}"
        streams.append(f"  {stream}:\n    - exec:{script}")
        preload.append(f'  {stream}: ""')

    if devices:
        print(
            "nooie: streaming "
            + ", ".join(f"nooie/{slug}" for slug in sorted(used)),
            file=sys.stderr,
        )

    with open(CONFIG, "w") as handle:
        handle.write(
            f"""api:
  listen: "0.0.0.0:{PORT_API}"
rtsp:
  listen: "0.0.0.0:{PORT_RTSP}"
webrtc:
  listen: ":{PORT_WEBRTC}/tcp"
  ice_servers: []
preload:
{chr(10).join(preload) or "  # no cameras yet"}
streams:
{chr(10).join(streams) or "  # no cameras yet"}
"""
        )

    os.execv(GO2RTC, [GO2RTC, "-c", CONFIG])


if __name__ == "__main__":
    main()

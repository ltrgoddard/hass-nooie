#!/usr/bin/env python3
"""onboard the throwaway home assistant and add the nooie integration.

a fresh install answers 404 on everything until a user exists, so this walks
/api/onboarding first, then starts the config flow with the credentials in
the checkout's .env. the token it leaves behind reaches the rest api.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = os.environ.get("HA_BASE", "http://127.0.0.1:8123")
CLIENT = f"{BASE}/"
RIG = Path(os.environ.get("RIG", "/tmp/ha-nooie"))
REPO = Path(__file__).resolve().parents[3]
USER, PASSWORD = "rig", "nooie-rig"


def dotenv(path: Path) -> dict[str, str]:
    found = {}
    for raw in path.read_text().splitlines():
        line = raw.strip().removeprefix("export ").strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            found[key.strip()] = value.strip().strip("\"'")
    return found


def call(path, payload=None, token=None, form=False):
    data, headers = None, {}
    if payload is not None:
        kind = "x-www-form-urlencoded" if form else "json"
        data = (urllib.parse.urlencode if form else json.dumps)(payload)
        headers["Content-Type"] = f"application/{kind}"
        data = data.encode()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(BASE + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            body = response.read().decode()
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


secrets = dotenv(REPO / ".env")
status, result = call(
    "/api/onboarding/users",
    {
        "client_id": CLIENT,
        "name": "Rig",
        "username": USER,
        "password": PASSWORD,
        "language": "en",
    },
)
if status != 200:
    sys.exit(f"onboarding refused the user: {status} {result}")

status, tokens = call(
    "/auth/token",
    {
        "grant_type": "authorization_code",
        "code": result["auth_code"],
        "client_id": CLIENT,
    },
    form=True,
)
token = tokens["access_token"]
for path, payload in (
    ("/api/onboarding/core_config", {}),
    ("/api/onboarding/analytics", {}),
    ("/api/onboarding/integration", {"client_id": CLIENT, "redirect_uri": CLIENT}),
):
    print(f"onboard {path.rsplit('/', 1)[-1]}:", call(path, payload, token=token)[0])

# the first sign-in builds the engine's environment, which takes a minute.
status, flow = call(
    "/api/config/config_entries/flow",
    {"handler": "nooie", "show_advanced_options": False},
    token=token,
)
print("start flow:", status, flow.get("step_id") if isinstance(flow, dict) else flow)
status, done = call(
    f"/api/config/config_entries/flow/{flow['flow_id']}",
    {
        "username": secrets["NOOIE_USERNAME"],
        "password": secrets["NOOIE_PASSWORD"],
        "country_code": secrets.get("NOOIE_COUNTRY_CODE", "44"),
    },
    token=token,
)
told = ("type", "title", "errors", "reason")
if isinstance(done, dict):
    done = {key: done.get(key) for key in told}
print("submit flow:", status, done)

(RIG / "token").write_text(token)
print(f"\nlog in at {BASE} as {USER} / {PASSWORD}")

#!/bin/sh
# build a throwaway home assistant that loads this integration, and start it
# beside a go2rtc, as a real install runs.
set -eu
RIG=${RIG:-/tmp/ha-nooie}
SKILL=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$SKILL/../../.." && pwd)
BIN=$RIG/venv/bin
GO2RTC=1.9.14

mkdir -p "$RIG/config/custom_components"

[ -x "$BIN/hass" ] || {
  echo "building the home assistant environment in $RIG/venv"
  uv venv --quiet "$RIG/venv"
  uv pip install --quiet --python "$BIN/python" homeassistant
}

# home assistant starts a go2rtc only in docker, so a venv install needs one
# on PATH. the release binary is the same one the container carries.
[ -x "$BIN/go2rtc" ] || {
  # the mac builds are zipped and the linux ones are not.
  case "$(uname -sm)" in
  "Darwin arm64") build=mac_arm64.zip ;;
  "Darwin x86_64") build=mac_amd64.zip ;;
  "Linux aarch64") build=linux_arm64 ;;
  *) build=linux_amd64 ;;
  esac
  url=https://github.com/AlexxIT/go2rtc/releases/download/v$GO2RTC/go2rtc_$build
  case "$build" in
  *.zip)
    curl -fsSL -o "$RIG/go2rtc.zip" "$url"
    unzip -qo "$RIG/go2rtc.zip" -d "$BIN" && rm "$RIG/go2rtc.zip"
    ;;
  *) curl -fsSL -o "$BIN/go2rtc" "$url" ;;
  esac
  chmod +x "$BIN/go2rtc"
}

# a symlink, so an edit in the checkout is live at the next restart.
ln -sfn "$REPO/custom_components/nooie" "$RIG/config/custom_components/nooie"
[ -f "$RIG/go2rtc.yaml" ] || cp "$SKILL/go2rtc.yaml" "$RIG/go2rtc.yaml"
[ -f "$RIG/config/configuration.yaml" ] || cat >"$RIG/config/configuration.yaml" <<'YAML'
default_config:

logger:
  default: warning
  logs:
    custom_components.nooie: debug
    homeassistant.components.go2rtc: debug

# the go2rtc beside this one; home assistant manages its own only in docker.
go2rtc:
  url: http://127.0.0.1:1984
YAML

pkill -f "$BIN/" 2>/dev/null || true
"$BIN/go2rtc" -config "$RIG/go2rtc.yaml" >"$RIG/go2rtc.log" 2>&1 &
# ffmpeg comes from PATH, for go2rtc and for the stream component alike.
PATH="$BIN:/opt/homebrew/bin:$PATH" \
  "$BIN/hass" -c "$RIG/config" --log-file "$RIG/ha.log" >"$RIG/stdout.log" 2>&1 &

printf 'starting home assistant'
until curl -fsS -o /dev/null http://127.0.0.1:8123/ 2>/dev/null; do
  printf .
  sleep 2
done
echo " up on http://127.0.0.1:8123"

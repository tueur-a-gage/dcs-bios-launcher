#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source private environment variables
source "$script_dir/.private"

build_folder="$DCS_BIOS_LAUNCHER_FOLDER/dcs-bios-launcher/build"
dist_folder="$DCS_BIOS_LAUNCHER_FOLDER/dcs-bios-launcher/dist"

echo
echo "== Creating build and dist directories if needed"
echo
mkdir -pv "$build_folder"
mkdir -pv "$dist_folder"

echo
echo "== Building dcs-bios-launcher"
echo

# Use this Windows image because we are targeting a Windows executable
if [[ -z "${DOCKER_REPO:-}" ]]; then
  DOCKER_IMAGE="batonogov/pyinstaller-windows"
else
  DOCKER_IMAGE="$DOCKER_REPO/batonogov/pyinstaller-windows"
fi

docker run --rm \
  --network host \
  -e HTTP_PROXY=$http_proxy \
  -e HTTPS_PROXY=$https_proxy \
  -e NO_PROXY=$no_proxy \
  -e http_proxy=$http_proxy \
  -e https_proxy=$https_proxy \
  -e no_proxy=$no_proxy \
  -e XDG_RUNTIME_DIR=/tmp \
  -e PIP_DEFAULT_TIMEOUT=100 \
  -v "$script_dir:/src" \
  -v "$build_folder:/src/build" \
  -v "$dist_folder:/src/dist" \
  "$DOCKER_IMAGE" \
  "pyinstaller --onefile $PRODUCTION --name DCS-BIOS-Launcher --add-data 'usb_icon.ico;.' --add-data 'vfa103.png;.' dcs-bios-launcher.py"
  # "python -m pip install --upgrade pip && python -m pip install --retries 10 --timeout 100 -r requirements.txt && pyinstaller --onefile $PRODUCTION --name DCS-BIOS-Launcher --add-data 'usb_icon.ico;.' --add-data 'vfa103.png;.' dcs-bios-launcher.py"

# If need to update pip and install requirements before building, use this command instead:
# docker run --rm \
#   -v "$(pwd):/src" \
#   -v "$build_folder:/src/build" \
#   -v "$dist_folder:/src/dist" \
#   batonogov/pyinstaller-windows \
#   "python -m pip install --upgrade pip && pip install -r requirements.txt && pyinstaller --onefile $PRODUCTION --name DCS-BIOS-Launcher --add-data 'usb_icon.ico;.' dcs-bios-launcher.py"

echo
echo "== Copying config.ini to dist folder"
echo
cp -v "$script_dir/config.ini" "$dist_folder/config.ini"

echo
echo "== Updating config.ini with SOCAT path"
echo
sed -i "s|TO-BE-POPULATED|$DCS_BIOS_FOLDER|" "$dist_folder/config.ini"

  set -e

# Source private environment variables
source .private

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
if [[ -z DOCKER_REPO ]]; then
  DOCKER_REPO="batonogov/pyinstaller-windows"
else
  DOCKER_REPO="$DOCKER_REPO/batonogov/pyinstaller-windows"
fi

docker run --rm \
  -v "$(pwd):/src" \
  -v "$build_folder:/src/build" \
  -v "$dist_folder:/src/dist" \
  "$DOCKER_REPO" \
  "pyinstaller --onefile $PRODUCTION --name DCS-BIOS-Launcher --add-data 'usb_icon.ico;.' --add-data 'vfa103.png;.' dcs-bios-launcher.py"

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
cp -v config.ini "$dist_folder/config.ini"

echo
echo "== Updating config.ini with SOCAT path"
echo
sed -i "s|TO-BE-POPULATED|$DCS_BIOS_FOLDER|" "$dist_folder/config.ini"

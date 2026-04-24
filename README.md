# DCS-BIOS Launcher

## Introduction

This project aims to launch DCS-BIOS using a graphical interface.

DCS-BIOS is now maintain by [DCS-Skunkworks](https://github.com/DCS-Skunkworks/dcs-bios/) and a continuation of [original DCS-BIOS](https://github.com/dcs-bios/dcs-bios) which is no longer updated.

To quickly summurized, it consist of Powershell scripts which allows to establish communication between your **USB Ports** (on which your module are plugged) and **dcs-bios library** using **SOCAT**.

This project try to redo the same things using **Python** and offer a graphical interface to scan the USB ports available and choose which one have to be linked to DCS Bios.

## Environment configuration

### Python installation and configuration

ℹ️ Under Windows, use the version provided by the **Windows Store**.

Create Python virtual environment named `.venv`

```bash
python -m venv .venv
```

#### Under Windows with Power shell

```powershell
.venv\Scripts\Activate.ps1
```

ℹ️ Under **Powershell** (like with **VSCode**), `.venv\Scripts\Activate.ps1` could not work because **ps1** scripts are deactivated by default.

Check rights with:

```powershell
Get-ExecutionPolicy
```

By default, under Win10/11: `Restricted`, change it for `RemoteSigned` to activate *venv*:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate *venv*:

```powershell
.venv\Scripts\Activate.ps1
```

#### Undex Windows Cmd

```cmd
.venv\Scripts\activate
```

#### Under Linux

```bash
source .venv/bin/activate
```

### Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### Install requirements

```powershell
pip install -r requirements.txt
```

check using:

```powershell
pip list
```

## Build application for Windows

## Application Configuration

Configure path for **SOCAT** in `config.ini`

For example: 

```ini
SOCAT = D:\MonDrive\Projets\dcs-bios\Programs\socat\socat.exe
```

## Generate binary

Binary should be build using **pyinstaller** for Windows. 

Under Linux, you could use a docker image for that: `batonogov/pyinstaller-windows`. 

Sources: <https://github.com/batonogov/docker-pyinstaller>

```bash
build_folder=<your_own_build>
dist_folder=<your_own_dist>

mkdir -pv $build_folder
mkdir -pv $dist_folder

docker run --rm \
  -v "$(pwd):/src" \
  -v "$build_folder:/src/build" \
  -v "$dist_folder:/src/dist" \
  batonogov/pyinstaller-windows \
  "python -m pip install --upgrade pip && pip install -r requirements.txt && pyinstaller --onefile --windowed --name DCS-BIOS-Launcher --add-data 'usb_icon.ico;.' dcs-bios-launcher.py"

cp config.ini $dist_folder/config.ini
```

The executable file will be in **your_own_dist/dcs-bios-launcher/dist** folder.

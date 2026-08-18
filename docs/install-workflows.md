# Installing PyDevices

This guide covers PyDevices products. For general `mip`, `micropython -m mip`,
and `mpremote mip` usage, see the [PyDevices MIP index](https://github.com/PyDevices/mip).

## System prerequisites (desktop)

The desktop backends need SDL2 from the system package manager before the Python
packages are installed:

```bash
sudo apt update && sudo apt install libsdl2-dev python3-venv   # Debian / Ubuntu / WSL
```

Fedora uses `SDL2-devel`; macOS uses Homebrew's `sdl2`. On Windows, install
Python from python.org — `pygame-ce` (`PGDisplay`) is generally the easiest
window backend there, and WSL supports the Linux workflow unchanged.

Headless CI should set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy`. For
Linux without X11 or Wayland, install the `board_configs/sdldisplay/linux_kms`
board config, which sets `SDL_VIDEODRIVER=kmsdrm` before SDL initializes; the
host needs an SDL build with KMSDRM support, access to `/dev/dri`, and no
competing DRM master.

| Target | Selection | Use case |
|---|---|---|
| Normal desktop | X11 / Wayland default | Desktop session |
| KMS | `SDL_VIDEODRIVER=kmsdrm` | Direct scanout with no window manager |
| Headless CI | `SDL_VIDEODRIVER=dummy` | Automated tests |

## Desktop with pip

One command installs the complete desktop runtime: all portable PyDevices
components, the desktop board configuration, and the bundled utility modules.

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pydevices-desktop
```

`pydevices-desktop` depends on `pydevices`; no extra is required. Verify the
board and utility entry points in a fresh environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pydevices-desktop
python -c "import board_config, micropython, mip; print(board_config.__file__)"
```

Install only the portable runtime when no desktop board is wanted:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pydevices
```

## MicroPython hardware board

Board installers live in this repository rather than the MIP index. Select the
matching directory and install it directly from GitHub while passing the
PyDevices index for its `pydevices` dependency:

```python
import mip

mip.install(
    "github:PyDevices/pydevices/board_configs/busdisplay/i80/t-display-s3",
    index="https://PyDevices.github.io/mip",
)
```

Each board installer includes its board-specific Python display, touch, and
peripheral drivers. It does not pull optional Python bus fallbacks when the
firmware is expected to provide the hardware interface.

## Desktop with MicroPython MIP

The desktop raw-GitHub installer is retained and depends on the indexed
`pydevices-desktop` package:

```bash
micropython -m mip install \
  --index https://PyDevices.github.io/mip \
  github:PyDevices/pydevices/board_configs/desktop
```

Use `--target lib` when installing into a workspace whose import path expects a
`lib/` directory. Add `--no-mpy` when the same tree must be readable by
CircuitPython or CPython.

## Connected-device installation

`mpremote` can perform the same hardware-board install without running `mip`
on the device:

```bash
mpremote mip install \
  --index https://PyDevices.github.io/mip \
  github:PyDevices/pydevices/board_configs/busdisplay/i80/t-display-s3
```

The recommended hosted-runtime search paths keep frozen firmware modules ahead
of workspace fallbacks:

```bash
export MICROPYPATH=".:.frozen:lib:utils:~/.micropython/lib:/usr/lib/micropython"
export PYTHONPATH=".:lib:utils"
```

This is why installing the CPython `micropython.py` compatibility module is
harmless on MicroPython: `.frozen` resolves first in the preferred path.

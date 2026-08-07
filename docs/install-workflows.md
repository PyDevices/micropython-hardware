# Install workflows

Canonical install and verification flows for MicroPython MCU board configs,
desktop `board_config`, and `pydisplay-desktop`.

## MicroPython MCU board_config via MIP

Install the matching board config directory from this repo and let `deps` pull
automatically from the PyDevices MIP index.

```python
import mip

INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install(
    "github:PyDevices/micropython-hardware/board_configs/busdisplay/i80/t-display-s3",
    index=INDEX,
)
```

Notes:
- This is the standard MCU flow.
- When `index=INDEX` is set, package dependencies resolve automatically (for
  example `displaysys` -> `eventsys` -> `multimer`).

## Desktop board_config via MIP

Use this flow for desktop-like hosts with `micropython` or `micropython.exe`.

```python
import mip

INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install(
    "github:PyDevices/micropython-hardware/board_configs/desktop",
    index=INDEX,
    target="lib",
)
import board_config
```

If you want local script-first installs in the current directory, use
`target="."` instead of `target="lib"`.

Expected files from the desktop board package:
- `board_config.py`
- `board_devices.py`
- `boarddev.py`
- `audiodev.py`
- `sdl2audio.py`
- `pygameaudio.py`
- `webaudio.py`

CircuitPython note:
- Our current `micropython-lib` clone/index does not build CircuitPython-compatible
    `.mpy` files.
- If `.mpy` dependencies are installed, CircuitPython can fail with:
    `ValueError: MicroPython .mpy file; use CircuitPython mpy-cross`

Quick verification (catches omitted split files):

```python
import board_config
import board_devices

print(board_config.__file__)
print(board_devices.__file__)
print(board_config.DEVICES)
```

## CircuitPython-compatible install via MicroPython `mip`

CircuitPython does not provide `mip`, so install package dependencies with
MicroPython and force source `.py` files (no `.mpy`) using `mpy=False`.

Run from your target working directory (for example `/tmp/my-cpy-run`):

```python
import mip

INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install(
    "github:PyDevices/micropython-hardware/board_configs/desktop",
    index=INDEX,
    target="lib",
    mpy=False,
)
```

Then run CircuitPython from that same directory so it imports from `./lib`.

Quick check:

```python
import board_config
import board_devices
print(board_config.__file__)
print(board_devices.__file__)
```

## pydisplay-desktop via pip

Install `pydisplay-desktop` directly from TestPyPI (not through another repo's
`requirements.txt`).

```bash
python -m pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple \
    pydisplay-desktop
```

Verify:

```python
import board_config
```

## Verify with .venv

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple \
    pydisplay-desktop
python - <<'PY'
import board_config
print(board_config.__file__)
print('display_drv', type(board_config.display_drv).__name__)
print('runtime', board_config.runtime is not None)
print('DEVICES', board_config.DEVICES)
PY
```

## Verify without .venv (python.exe / pip.exe)

```bash
python.exe -m pip install --user \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple \
    pydisplay-desktop

# Optional refresh to force current TestPyPI artifact ownership
python.exe -m pip install --user \
    --index-url https://test.pypi.org/simple/ \
    --force-reinstall --no-deps \
    pydisplay-desktop

python.exe - <<'PY'
import board_config
print(board_config.__file__)
print('display_drv', type(board_config.display_drv).__name__)
print('runtime', board_config.runtime is not None)
print('DEVICES', board_config.DEVICES)
PY
```

`pip.exe` should resolve to the same interpreter as `python.exe` for
consistent results.
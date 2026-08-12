# Install workflows

Canonical install and verification flows for MicroPython MCU board configs,
desktop `board_config`, and `pydevices-desktop`.

## MicroPython MCU board_config via MIP

Install the matching board config directory from this repo and let `deps` pull
automatically from the PyDevices MIP index.

```python
import mip

INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install(
    "github:PyDevices/pydevices/board_configs/busdisplay/i80/t-display-s3",
    index=INDEX,
)
```

Notes:
- This is the standard MCU flow.
- When `index=INDEX` is set, package dependencies resolve automatically (for
  example `displaydev` → `events` + `keys`; `eventsys` → `events` + `keys` + `multimer`).

## Desktop board_config via MIP

Preferred for desktop-like hosts with `micropython` or `micropython.exe`: the
`-m mip` CLI. Run from the directory that should own `./lib` (for example
`~/.micropython`, or `/tmp` for a scratch install). Always pass `-i` so deps
resolve from the PyDevices index (without it, deps fall back to
`micropython.org/pi/v2` and fail).

**`--no-mpy` vs precompiled `.mpy`:**
- Omit `--no-mpy` when the install is for MicroPython only — mip downloads
  precompiled `.mpy` from the index (smaller / faster imports).
- Pass `--no-mpy` when the same `lib/` tree will also be used by CircuitPython
  (preferred for shared installs). CircuitPython cannot load MicroPython
  `.mpy` files.

MicroPython-only (precompiled `.mpy`):

```bash
micropython -m mip install -t lib \
  -i https://PyDevices.github.io/micropython-lib/mip/PyDevices \
  github:PyDevices/pydevices/board_configs/desktop
```

Shared with CircuitPython (source `.py`):

```bash
micropython -m mip install --no-mpy -t lib \
  -i https://PyDevices.github.io/micropython-lib/mip/PyDevices \
  github:PyDevices/pydevices/board_configs/desktop
```

Same commands with `micropython.exe` on Windows. Pin a branch with
`…/desktop@main` if you want an explicit ref.

REPL equivalent (shared / source install shown; drop `mpy=False` for
precompiled):

```python
import mip

INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install(
    "github:PyDevices/pydevices/board_configs/desktop",
    index=INDEX,
    target="lib",
    mpy=False,  # omit for MicroPython-only .mpy installs
)
```

If you want local script-first installs in the current directory, use
`-t .` / `target="."` instead of `lib`.

Expected files from the desktop board package:
- `board_config.py`
- `board_peripherals.py`
- `boarddev.py`
- `audiodev/` (package)
- `usdl2.py`
- `uwin32.py` (Windows CPython)

CircuitPython note:
- Our `micropython-lib` clone/index does not build CircuitPython-compatible
  `.mpy` files.
- If `.mpy` dependencies are installed, CircuitPython can fail with:
  `ValueError: MicroPython .mpy file; use CircuitPython mpy-cross`

Quick verification (catches omitted split files):

```python
import board_config
import board_peripherals

print(board_config.__file__)
print(board_peripherals.__file__)
print(board_config.PERIPHERALS)
```

## CircuitPython-compatible install via MicroPython `mip`

CircuitPython does not provide `mip`, so install with MicroPython using the
shared-install CLI from [Desktop board_config via MIP](#desktop-board_config-via-mip)
(`--no-mpy`, `-t lib`, PyDevices `-i`). Prefer `--no-mpy` whenever that `lib/`
will be imported by CircuitPython; omit it only for MicroPython-only trees
that should use precompiled `.mpy`.

Run from your target working directory (for example `/tmp/my-cpy-run`):

```bash
micropython -m mip install --no-mpy -t lib \
  -i https://PyDevices.github.io/micropython-lib/mip/PyDevices \
  github:PyDevices/pydevices/board_configs/desktop
```

Then run CircuitPython from that same directory so it imports from `./lib`.

Quick check:

```python
import board_config
import board_peripherals
print(board_config.__file__)
print(board_peripherals.__file__)
```

## pydevices-desktop via pip

Install `pydevices-desktop` directly from TestPyPI (not through another repo's
`requirements.txt`).

```bash
python -m pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple \
    pydevices-desktop
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
    pydevices-desktop
python - <<'PY'
import board_config
print(board_config.__file__)
print('display_drv', type(board_config.display_drv).__name__)
print('host_read', callable(board_config.host_read))
print('runtime in board_config', hasattr(board_config, 'runtime'))  # False
print('PERIPHERALS', board_config.PERIPHERALS)
PY
```

## Verify without .venv (python.exe / pip.exe)

```bash
python.exe -m pip install --user \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple \
    pydevices-desktop

# Optional refresh to force current TestPyPI artifact ownership
python.exe -m pip install --user \
    --index-url https://test.pypi.org/simple/ \
    --force-reinstall --no-deps \
    pydevices-desktop

python.exe - <<'PY'
import board_config
print(board_config.__file__)
print('display_drv', type(board_config.display_drv).__name__)
print('host_read', callable(board_config.host_read))
print('runtime in board_config', hasattr(board_config, 'runtime'))  # False
print('PERIPHERALS', board_config.PERIPHERALS)
PY
```

`pip.exe` should resolve to the same interpreter as `python.exe` for
consistent results.

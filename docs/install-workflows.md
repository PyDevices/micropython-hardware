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
- The default index in `mip` is upstream `https://micropython.org/pi/v2`. By passing `index="https://PyDevices.github.io/micropython-lib/mip/PyDevices"`, `mip` resolves packages from the PyDevices custom package index (built from the `PyDevices/micropython-lib` fork).
- When `index=INDEX` is set, dependencies resolve automatically (for example `displaydev` → `events` + `keys`; `eventsys` → `events` + `keys` + `multimer`).
- The PyDevices index hosts both precompiled `.mpy` bytecode and raw `.py` sources.

## Desktop board_config via MIP

Preferred for desktop-like hosts with `micropython` or `micropython.exe`: the `-m mip` CLI. 

To set up a local desktop simulation workspace, create your preferred directory (such as `~/.micropython` or `%USERPROFILE%\.micropython`), `cd` into it, and run `mip` targeting the `lib` folder:

```bash
# On Linux / macOS
mkdir -p ~/.micropython && cd ~/.micropython
micropython -m mip install --target lib --index https://PyDevices.github.io/micropython-lib/mip/PyDevices github:PyDevices/pydevices/board_configs/desktop

# On Windows (cmd.exe)
mkdir "%USERPROFILE%\.micropython" && cd "%USERPROFILE%\.micropython"
micropython.exe -m mip install --target lib --index https://PyDevices.github.io/micropython-lib/mip/PyDevices github:PyDevices/pydevices/board_configs/desktop
```

#### Preferred Environment Variables
For details on the preferred `PYTHONPATH` and `MICROPYPATH` environment variables and the rationale behind their layout, see [Preferred Path Configuration in the flagship pydevices README](../../README.md#preferred-path-configuration).



**`--no-mpy` vs precompiled `.mpy`:**
- Omit `--no-mpy` when the install is for MicroPython only — `mip` downloads precompiled `.mpy` bytecode from the PyDevices index for faster imports and lower RAM usage.
- Pass `--no-mpy` when source inspection is needed or when the same `lib/` tree will also be used by CircuitPython (preferred for shared installs). CircuitPython cannot load MicroPython `.mpy` files.

Shared with CircuitPython (source `.py`):

```bash
micropython -m mip install --no-mpy --target lib \
  --index https://PyDevices.github.io/micropython-lib/mip/PyDevices \
  github:PyDevices/pydevices/board_configs/desktop
```

REPL equivalent (shared / source install shown; drop `mpy=False` for precompiled):

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

Expected files and directories in `lib/` after desktop board package installation:
- `board_config.py` (Source)
- `board_peripherals.py` (Source)
- `boarddev.py` (Source)
- `displaydev/` (Compiled `.mpy` or source `.py`)
- `audiodev/` (Compiled `.mpy` or source `.py`)
- `multimer/` (Compiled `.mpy` or source `.py`)
- `eventsys/` (Compiled `.mpy` or source `.py`)
- `uwin32.mpy` / `uwin32.py`
- `usdl2.mpy` / `usdl2.py`
- `events.mpy` / `events.py`
- `keys.mpy` / `keys.py`
- `utils/` (Compiled `.mpy` or source `.py`)


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

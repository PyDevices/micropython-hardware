# pydevices

The flagship display engine, hardware driver suite, and board configuration standard for [PyDevices](https://github.com/PyDevices).

`pydevices` is the canonical source and publisher for cross-runtime hardware drivers, board configurations, and pure-Python core packages:
`displaydev`, `audiodev`, optional `eventsys`, `multimer`, `events`, and `keys`.

---

## Key Concepts

### The PyDevices Board Contract
PyDevices hardware drivers and board configurations adhere to a standardized contract across target boards:
- **Eager UI Hardware (`board_config.py`)**: Initializes display, touch, and primary UI inputs immediately upon import, exporting standard handles like `display_drv` and capability flags.
- **Lazy Extra Peripherals (`board_peripherals.py` / `boarddev`)**: Defers initialization of secondary hardware (sensors, external flash, power monitoring) until explicitly requested by the application via `boarddev`.
- **Decoupled Application Lifecycle**: Board configuration exports neutral capability interfaces; event coordination and application flow remain strictly owned by the application.

### Cross-Runtime Compatibility
Write your display and hardware logic once and run across 5 supported Python environments:
1. **MicroPython** — Microcontroller firmware with MIP package support.
2. **CircuitPython** — Microcontroller firmware with stock driver compatibility.
3. **CPython (Desktop)** — Native desktop development and testing (`pydevices-desktop`).
4. **PyScript / Pyodide (Web PWA)** — Web browser deployment without code changes.
5. **Android (APK)** — Mobile package deployment via Buildozer (`pydevices-android-template`).

---

## Layout

| Path | Contents |
|------|----------|
| `board_configs/` | MicroPython boards (top level); CircuitPython under `board_configs/cp/` |
| `drivers/` | Display, touch, bus, joystick, IO expander, input helpers |
| `lib/displaydev/` | Display backends (`BusDisplay`, `SDLDisplay`, …); `auto.py` is convenience only |
| `lib/` | `audiodev/`, `displaydev/`, `eventsys/`, `events.py`, `keys.py`, `multimer/` |
| `utils/` | Portable helpers (`byteswap`, `mip`, `viper_tools`, `keypins`, `wifi`, `frame_recorder`, CPython `micropython` shim) |
| `packages/` | Shared MIP manifests (`displaydev`, `utils`, `spibus`, `i80bus`, …) |
| `tests/` | Stdlib unittest for `displaydev`, `multimer`, `events`, `keys`, `audiodev`, `boarddev`, `mip` |
| `docs/` | Hardware & Board Contract documentation ([Pages](https://pydevices.github.io/pydevices/)) |

## Documentation

Full specification, driver matrix, and board contract details are available on GitHub Pages:
[pydevices.github.io/pydevices](https://pydevices.github.io/pydevices/)

- [Board Contract Specification](docs/board-peripherals.md)
- [Board Configuration Inventory](docs/board-inventory.md)
- [Hardware Driver Inventory](docs/driver-inventory.md)
- [Cross-Platform Architecture](docs/architecture.md)

## Installation

### 1. Desktop / Simulation Quickstart (MicroPython)
To quickly set up a local desktop simulation and development workspace, download `micropython` or `micropython.exe` to your machine and run the following three commands to generate a ready-to-use workspace:

```bash
# On Linux / macOS
mkdir -p ~/.micropython && cd ~/.micropython
micropython -m mip install --target lib --index https://PyDevices.github.io/micropython-lib/mip/PyDevices github:PyDevices/pydevices/board_configs/desktop

# On Windows (cmd.exe)
mkdir "%USERPROFILE%\.micropython" && cd "%USERPROFILE%\.micropython"
micropython.exe -m mip install --target lib --index https://PyDevices.github.io/micropython-lib/mip/PyDevices github:PyDevices/pydevices/board_configs/desktop
```

#### Preferred Path Configuration
When running your application or script, set the following environment variables:

```bash
# On Linux / macOS (bash)
export MICROPYPATH=".:.frozen:lib:utils:~/.micropython/lib:/usr/lib/micropython"
export PYTHONPATH=".:lib:utils"

# On Windows (cmd.exe)
set MICROPYPATH=.;.frozen;lib;utils;%USERPROFILE%\.micropython\lib
set PYTHONPATH=.;lib;utils
```

##### Why this setup?
This path configuration mimics the default search path on both hosted Unix/Windows runtimes and hardware MCUs (where `.frozen`, the user home `.micropython/lib`, and the system `/usr/lib/micropython` library are searched by default), but explicitly appends the local directories `.` (current folder), `lib` (local workspace), and `utils` (shared dev tools) to the path. This ensures that custom packages, simulator components, and examples are immediately runnable from any directory without path conflicts.



---

### 2. CPython Desktop (pip)
Install the CPython desktop simulation package and backend drivers:
```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pydevices[desktop]
```

---

### 3. Microcontroller Boards (MIP)
On MCU boards with network access, install the specific `board_config` directly to the device:
```python
import mip
mip.install("board_configs/esp32_s3_box", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```
For connected boards without network access, run installation via `mpremote`:
```bash
mpremote mip install --index https://PyDevices.github.io/micropython-lib/mip/PyDevices board_configs/esp32_s3_box
```
See [docs/install-workflows.md](docs/install-workflows.md) for full workflows and verification.


## Companion Showcases & Demos

For ready-to-run application examples, GUI gallery demos, and tutorial code using `pydevices`, see the [pydevices-examples](https://github.com/PyDevices/pydevices-examples) companion repository.

## Tests

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests -v
```
See [`tests/README.md`](tests/README.md).

## License

MIT — see [LICENSE](LICENSE).


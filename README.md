# pydevices

Board configs and hardware drivers for [PyDevices](https://github.com/PyDevices)
on MicroPython and CircuitPython (display, touch, bus, input, …).

This repo holds board configs, hardware drivers, and shared pure-Python
packages used by both firmware and [pydevices-examples](https://github.com/PyDevices/pydevices-examples):
`displaydev`, `audiodev`, optional `eventsys`, `multimer`, `events`, and `keys`.
This repo is their canonical source and publisher. Optional host display
selection is `displaydev.auto` only — backends never import it.

The portable TestPyPI bundle is `pydevices`; add its `desktop` extra or install
exactly one MIP board package when a board selection is needed.

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
| `docs/` | Hardware documentation (markdown; published on GitHub Pages, not RTD) |

Documentation:
[pydevices.github.io/pydevices](https://pydevices.github.io/pydevices/)
(board configs, board-peripherals contract, drivers, inventories, device matrix).

Graduated campaign boards use the
[board peripherals contract](https://pydevices.github.io/pydevices/board-peripherals.html):
eager UI hardware in `board_config.py`, lazy extras in `board_peripherals.py` via
the local `boarddev`. Event coordination belongs to the application.

## Install (MIP)

See the canonical install/verify guide:
[docs/install-workflows.md](docs/install-workflows.md)

Package ownership, naming, and releases are documented in
[docs/publishing.md](docs/publishing.md).

For MCU boards, the standard flow is: install the matching `board_config`
directory via MIP with the PyDevices index and let `deps` resolve automatically.

## Desktop / browser configs

`board_configs/{sdldisplay,pgdisplay,windisplay,jndisplay,psdisplay}/` remain here for
MIP/path consistency. The universal desktop config is now
`board_configs/desktop/` for MIP installs and `pydevices-desktop` for pip/TestPyPI
installs, keeping the desktop flow analogous across package managers.

## Tests

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests -v
```

See [`tests/README.md`](tests/README.md).

## License

MIT — see [LICENSE](LICENSE).

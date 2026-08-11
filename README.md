# micropython-hardware

Board configs and hardware drivers for [PyDevices](https://github.com/PyDevices)
on MicroPython and CircuitPython (display, touch, bus, input, …).

This repo holds what used to live under pydisplay’s `board_configs/`,
`drivers/`, and bus/touch MIP manifests. The pure-Python core (`displaysys`,
`eventsys`, `graphics`, `boarddev`, …) stays in
[pydisplay](https://github.com/PyDevices/pydisplay).

## Layout

| Path | Contents |
|------|----------|
| `board_configs/` | MicroPython boards (top level); CircuitPython under `board_configs/cp/` |
| `drivers/` | Display, touch, bus, joystick, IO expander, input helpers |
| `packages/` | Shared MIP manifests for bus/touch/chip helpers (`spibus`, `i80bus`, …) |
| `docs/` | Hardware documentation (markdown; published on GitHub Pages, not RTD) |

Documentation:
[pydevices.github.io/micropython-hardware](https://pydevices.github.io/micropython-hardware/)
(board configs, board-devices contract, drivers, inventories, device matrix).

Graduated campaign boards use the
[board devices contract](https://pydevices.github.io/micropython-hardware/board-devices.html):
eager UI in `board_config.py`, lazy extras in `board_devices.py` via
pydisplay’s `boarddev`.

## Install (MIP)

See the canonical install/verify guide:
[docs/install-workflows.md](docs/install-workflows.md)

For MCU boards, the standard flow is: install the matching `board_config`
directory via MIP with the PyDevices index and let `deps` resolve automatically.

## Desktop / browser configs

`board_configs/{sdldisplay,pgdisplay,windisplay,jndisplay,psdisplay}/` remain here for
MIP/path consistency. The universal desktop config is now
`board_configs/desktop/` for MIP installs and `pydisplay-desktop` for pip/TestPyPI
installs, keeping the desktop flow analogous across package managers.

## License

MIT — see [LICENSE](LICENSE).

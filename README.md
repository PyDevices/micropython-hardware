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
| `board_configs/` | Per-board `board_config.py` (+ `board_devices.py` on graduated boards) and MIP `package.json` |
| `drivers/` | Display, touch, bus, encoder, joystick, IO expander helpers |
| `packages/` | Shared MIP manifests for bus/touch/chip helpers (`spibus`, `i80bus`, …) |

Graduated campaign boards use the
[board devices contract](https://pydisplay.readthedocs.io/en/latest/hardware/board-devices.html):
eager UI in `board_config.py`, lazy extras in `board_devices.py` via
pydisplay’s `boarddev`. Device matrix:
[Pages](https://pydevices.github.io/micropython-hardware/) /
[`device-matrix.md`](device-matrix.md).

## Install (MIP)

```python
import mip
mip.install("github:PyDevices/micropython-hardware/board_configs/fbdisplay/esp32-p4-wifi6-touch-lcd-4b")
# or a shared helper package:
mip.install("github:PyDevices/micropython-hardware/packages/spibus.json")
```

Also install pydisplay core packages (`displaysys`, `eventsys`, …) as listed in
each board’s `package.json` `deps`.
## Desktop / browser configs

`board_configs/{sdldisplay,pgdisplay,jndisplay,psdisplay}/` remain here for
MIP/path consistency. pydisplay’s default desktop config is still
`pydisplay/src/lib/board_config.py`.

## License

MIT — see [LICENSE](LICENSE).

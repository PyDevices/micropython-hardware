# Display drivers

MicroPython display controller drivers for use with `displaydev.busdisplay.BusDisplay`.

Source: [`drivers/display/`](https://github.com/PyDevices/pydevices/tree/main/drivers/display)

## Init sequence formats

Three formats are supported:

1. **CircuitPython DisplayIO bytearray** — e.g. [`gc9a01.py`](https://github.com/PyDevices/pydevices/blob/main/drivers/display/gc9a01.py)
2. **List of tuples** — e.g. [`st7789.py`](https://github.com/PyDevices/pydevices/blob/main/drivers/display/st7789.py)
3. **Manual init sequence** — e.g. [`st7796.py`](https://github.com/PyDevices/pydevices/blob/main/drivers/display/st7796.py)

## Constructor API

Drivers follow CircuitPython DisplayIO conventions, including rotation as `0`, `90`, `180`, `270` (not 0–3).

## Installing drivers

Board config packages install the drivers they need. To install individually:

```python
mip.install("github:PyDevices/pydevices/drivers/display/st7789.py", target="./drivers/display")
```

Precompiled drivers are also on the [micropython-lib index](../installation/mip-micropython-lib.md) (e.g. `mip.install("st7789", index=...)`).

## CircuitPython

On CircuitPython, prefer Adafruit's display drivers and the PyDevices `BusDisplay` wrapper — see [CircuitPython platform guide](https://github.com/PyDevices/pydevices-examples/blob/main/docs/platforms/circuitpython.md).

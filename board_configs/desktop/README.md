# desktop board_config

Universal non-MCU board config for desktop-like hosts.

## Install

Use the canonical install/verify guide:
[../../docs/install-workflows.md](../../docs/install-workflows.md)

For this package, follow the "Desktop board_config via MIP" section.

### CircuitPython note

Our current `micropython-lib` clone/index does not build CircuitPython-compatible
`.mpy` files. If `.mpy` dependencies are installed, CircuitPython can fail with:

`ValueError: MicroPython .mpy file; use CircuitPython mpy-cross`

CircuitPython does not provide `mip`, so install with MicroPython and force
source files:

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

Run CircuitPython from that same working directory so it imports from `./lib`.

## Use

```python
import board_config

display_drv = board_config.display_drv
runtime = board_config.runtime
```

`display_drv` and `runtime` are constructed at import time (same shape as MCU
board configs). Lazy audio roles still come from `board_devices`.

This bundle installs:
- `board_config.py`
- `board_devices.py`
- `boarddev.py`
- `audiodev.py`
- `sdl2audio.py`
- `usdl2.py`
- `pygameaudio.py`
- `webaudio.py`
- plus `displaysys`, `eventsys`, and `multimer` from the PyDevices MIP index

Display host selection is `displaysys.AutoDisplay`:
- PyScript: `PSDisplay`
- Jupyter: `JNDisplay`
- Desktop CPython/MicroPython unix/windows: `PGDisplay` first, then `SDLDisplay` fallback

Audio (in `board_devices`) follows the same host probe:
- PyScript: `webaudio`
- Jupyter: `sdl2audio` (kernel host)
- Desktop: `import pygame` → `pygameaudio`, else `sdl2audio`

Terminal-only apps (no display) can `import board_devices` and call
`audio_out()` / `audio_in()` without opening a window.

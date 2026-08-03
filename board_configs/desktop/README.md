# desktop board_config

Universal non-MCU board config for desktop-like hosts.

## Install

```python
import mip
INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install(
	"github:PyDevices/micropython-hardware/board_configs/desktop",
	index=INDEX,
)
```

For script-first workflows (including `micropython.exe` on host systems), use a
local target so the files land in the current directory:

```python
import mip
INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install(
	"github:PyDevices/micropython-hardware/board_configs/desktop",
	index=INDEX,
	target=".",
)
```

## Use

```python
import board_config

# Lazy init: display/audio setup occurs on first access.
display_drv = board_config.display_drv
runtime = board_config.runtime
```

This bundle installs:
- `board_config.py`
- `boarddev.py`
- `audiodev.py`
- `sdl2audio.py`
- plus `displaysys`, `eventsys`, and `multimer` from the PyDevices MIP index

`board_config.py` selects host behavior at runtime:
- PyScript: `PSDisplay`
- Jupyter: `JNDisplay`
- Desktop CPython/MicroPython unix/windows: `PGDisplay` first, then `SDLDisplay` fallback

# desktop board_config

Universal non-MCU board config for desktop-like hosts.

## Install

Use the canonical install/verify guide:
[../../docs/install-workflows.md](../../docs/install-workflows.md)

For this package, follow the "Desktop board_config via MIP" section.

## Use

```python
import board_config

# Lazy init: display/audio setup occurs on first access.
display_drv = board_config.display_drv
runtime = board_config.runtime
```

This bundle installs:
- `board_config.py`
- `board_devices.py`
- `boarddev.py`
- `audiodev.py`
- `sdl2audio.py`
- plus `displaysys`, `eventsys`, and `multimer` from the PyDevices MIP index

`board_config.py` selects host behavior at runtime:
- PyScript: `PSDisplay`
- Jupyter: `JNDisplay`
- Desktop CPython/MicroPython unix/windows: `PGDisplay` first, then `SDLDisplay` fallback

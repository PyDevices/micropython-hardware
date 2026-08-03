# desktop board_config

Universal non-MCU board config for desktop-like hosts.

## Install

```python
import mip
mip.install("github:PyDevices/micropython-hardware/board_configs/desktop")
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

`board_config.py` selects host behavior at runtime:
- PyScript: `PSDisplay`
- Jupyter: `JNDisplay`
- Desktop CPython/MicroPython unix/windows: `PGDisplay` first, then `SDLDisplay` fallback

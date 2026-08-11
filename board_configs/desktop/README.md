# desktop board_config

Universal non-MCU board config for desktop-like hosts.

## Install

Use the canonical install/verify guide:
[../../docs/install-workflows.md](../../docs/install-workflows.md)

For this package, follow the "Desktop board_config via MIP" section.

### CircuitPython note

Our `micropython-lib` clone/index does not build CircuitPython-compatible
`.mpy` files. If `.mpy` dependencies are installed, CircuitPython can fail with:

`ValueError: MicroPython .mpy file; use CircuitPython mpy-cross`

CircuitPython does not provide `mip`, so install with MicroPython using the
`-m mip` CLI. Prefer `--no-mpy` when sharing that `lib/` with CircuitPython;
omit `--no-mpy` for MicroPython-only installs to get precompiled `.mpy`.
Run from the directory that should own `./lib`:

```bash
# Shared with CircuitPython (source .py)
micropython -m mip install --no-mpy -t lib \
  -i https://PyDevices.github.io/micropython-lib/mip/PyDevices \
  github:PyDevices/micropython-hardware/board_configs/desktop

# MicroPython-only (precompiled .mpy) — omit --no-mpy
# micropython -m mip install -t lib -i … github:…/board_configs/desktop
```

Same with `micropython.exe` on Windows. See
[install-workflows.md](../../docs/install-workflows.md) for the full notes
and REPL equivalent.

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
- `audiodev/` (package)
- `usdl2.py`
- plus `displaysys`, `eventsys`, and `multimer` from the PyDevices MIP index

Display host selection is `displaysys.AutoDisplay`:
- PyScript: `PSDisplay`
- Jupyter: `JNDisplay`
- Desktop CPython/MicroPython unix/windows: `PGDisplay` first, then `SDLDisplay` fallback

Audio (in `board_devices`) follows the same host probe:
- PyScript: `web_audio`
- Jupyter: `sdl2_audio` (kernel host)
- Desktop: `import pygame` → `pygame_audio`, else `sdl2_audio`

Terminal-only apps (no display) can `import board_devices` and call
`audio_out()` / `audio_in()` without opening a window.

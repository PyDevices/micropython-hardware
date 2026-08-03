# pydisplay-desktop

Desktop bundle for non-MCU hosts using PyDevices display/runtime modules.

Installed modules:
- board_config
- boarddev
- audiodev
- sdl2audio

This package is intended to provide a single pip-installable desktop config
bundle while core runtime libraries continue to come from PyDevices packages.

## Install (TestPyPI)

```bash
python -m pip install \
	--index-url https://test.pypi.org/simple/ \
	--extra-index-url https://pypi.org/simple \
	pydisplay-desktop
```

After install:

```python
import board_config
```

`board_config` uses lazy initialization. Display/audio setup runs when runtime
objects are first accessed, not at import time.

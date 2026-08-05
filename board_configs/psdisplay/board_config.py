"""
Board configuration for PyScript.
"""

import os

from displaysys.psdisplay import PSDevices, PSDisplay
import eventsys

width = 320
height = 480


def _env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


width = _env_int("PYDISPLAY_WIDTH", width)
height = _env_int("PYDISPLAY_HEIGHT", height)

display_drv = PSDisplay("display_canvas", width, height)
devices_drv = PSDevices("display_canvas", display_drv)

runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=devices_drv.read,
    timer_async=True,
)

display_drv.fill(0)

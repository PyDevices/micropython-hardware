"""Universal non-MCU board configuration (desktop / Jupyter / PyScript)."""

import sys

from displaydev import env_bool, env_float, env_int
from displaydev.auto import AutoDisplay
import eventsys

_width = env_int("PYDISPLAY_WIDTH", 320)
_height = env_int("PYDISPLAY_HEIGHT", 480)
_rotation = env_int("PYDISPLAY_ROTATION", 0)
_scale = env_float("PYDISPLAY_SCALE", 2.0)

display_drv = AutoDisplay(
    width=_width,
    height=_height,
    rotation=_rotation,
    scale=_scale,
    title="{} on {}".format(sys.implementation.name, sys.platform),
)

runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=display_drv.get_events,
    timer_async=env_bool("PYDISPLAY_TIMER_ASYNC", display_drv.requires_async_timer),
)

display_drv.fill(0)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

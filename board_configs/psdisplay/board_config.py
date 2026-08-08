"""
Board configuration for PyScript.
"""

from displaysys import env_int
from displaysys.psdisplay import PSDisplay
import eventsys

width = 320
height = 480

width = env_int("PYDISPLAY_WIDTH", width)
height = env_int("PYDISPLAY_HEIGHT", height)

display_drv = PSDisplay("display_canvas", width, height)

runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=display_drv.get_events,
    timer_async=display_drv.requires_async_timer,
)

display_drv.fill(0)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

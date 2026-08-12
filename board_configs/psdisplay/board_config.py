"""
Board configuration for PyScript.
"""

from displaydev import env_int
from displaydev.psdisplay import PSDisplay

width = 320
height = 480

width = env_int("PYDISPLAY_WIDTH", width)
height = env_int("PYDISPLAY_HEIGHT", height)

display_drv = PSDisplay("display_canvas", width, height)

host_read = display_drv.get_events
timer_async = display_drv.requires_async_timer

display_drv.fill(0)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

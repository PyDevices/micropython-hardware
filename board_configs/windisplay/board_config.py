"""
Board configuration for Win32 (uwin32) desktop display.
"""

import sys

from displaysys.windisplay import WinDisplay as DTDisplay
import eventsys

width = 320
height = 480
rotation = 0
scale = 2.0

display_drv = DTDisplay(
    width=width,
    height=height,
    rotation=rotation,
    title=f"{sys.implementation.name} on {sys.platform}",
    scale=scale,
)

runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=display_drv.get_events,
)

display_drv.fill(0)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

"""
Board configuration for Jupyter Notebook.
"""

from displaysys.jndisplay import JNDisplay
import eventsys

width = 320
height = 480

display_drv = JNDisplay(width, height)

runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=display_drv.get_events,
    timer_async=display_drv.requires_async_timer,
)

display_drv.fill(0)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

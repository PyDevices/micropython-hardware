"""Seeed GC9A01 round display on QT Py ESP32-S3 — CircuitPython"""

from adafruit_focaltouch import Adafruit_FocalTouch
import board
from displayio import release_displays
from fourwire import FourWire
from gc9a01 import GC9A01

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D8,
    chip_select=board.D17,
    baudrate=60_000_000,
)

display_drv = GC9A01(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=True,
)
i2c = board.I2C()
touch = Adafruit_FocalTouch(i2c)


def _touch_points():
    touches = touch.touches
    if not touches:
        return ()
    return tuple((t["x"], t["y"]) for t in touches)


touch_rotation_table = (0, 5, 6, 3)

runtime = eventsys.Runtime(
    displays=[display_drv],
    touch_read=_touch_points,
    touch_rotation_table=touch_rotation_table,
)

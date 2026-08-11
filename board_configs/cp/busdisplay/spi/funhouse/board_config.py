"""Adafruit FunHouse ST7789 + TT21100 touch — CircuitPython"""

from adafruit_tt21100 import TT21100
import board
from displayio import release_displays
from fourwire import FourWire
from keypad_gpio import GPIOButtons
from st7789 import ST7789

import eventsys

import keys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.TFT_DC,
    chip_select=board.TFT_CS,
    baudrate=24_000_000,
    reset=board.TFT_RESET,
)

display_drv = ST7789(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=80,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
)
i2c = board.I2C()
touch = TT21100(i2c)


def _touch_points():
    touches = touch.touches
    if not touches:
        return ()
    return tuple((t["x"], t["y"]) for t in touches)


touch_rotation_table = (0, 0, 0, 0)

keypad = GPIOButtons(
    {
        "down": (board.BUTTON_DOWN, keys.K_DOWN),
        "select": (board.BUTTON_SELECT, keys.K_RETURN),
        "up": (board.BUTTON_UP, keys.K_UP),
    }
)

runtime = eventsys.Runtime(
    displays=[display_drv],
    touch_read=_touch_points,
    touch_rotation_table=touch_rotation_table,
)
runtime.add_keypad(read=keypad.read)

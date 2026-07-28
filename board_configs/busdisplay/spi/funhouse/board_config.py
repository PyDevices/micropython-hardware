"""Adafruit FunHouse ST7789 + TT21100 — MicroPython (ESP32-S2)"""

from keypad_gpio import GPIOButtons
from machine import I2C, Pin
from spibus import SPIBus
from st7789 import ST7789
from tt21100 import TT21100

import eventsys

try:
    from eventsys.keys import Keys
except ImportError:
    from keys import Keys

display_bus = SPIBus(
    id=1,
    baudrate=24_000_000,
    sck=36,
    mosi=35,
    miso=-1,
    command=39,
    chip_select=40,
    reset=41,
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
# Shared UI I2C: touch + AHT20 + BMP280 + STEMMA
i2c = I2C(0, sda=Pin(34), scl=Pin(33), freq=400_000)
touch = TT21100(i2c)


def _touch_points():
    touches = touch.touches
    if not touches:
        return ()
    return tuple((t["x"], t["y"]) for t in touches)


touch_rotation_table = (0, 0, 0, 0)

# BUTTON_DOWN=3, BUTTON_SELECT=4, BUTTON_UP=5
keypad = GPIOButtons(
    {
        "down": (Pin(3, Pin.IN, Pin.PULL_UP), Keys.K_DOWN),
        "select": (Pin(4, Pin.IN, Pin.PULL_UP), Keys.K_RETURN),
        "up": (Pin(5, Pin.IN, Pin.PULL_UP), Keys.K_UP),
    }
)

runtime = eventsys.Runtime(
    displays=[display_drv],
    touch_read=_touch_points,
    touch_rotation_table=touch_rotation_table,
)
runtime.add_keypad(read=keypad.read)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

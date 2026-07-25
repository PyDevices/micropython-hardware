"""Adafruit CLUE ST7789 — MicroPython (nRF52840)"""

from keypad_gpio import GPIOButtons
from machine import I2C, Pin
from spibus import SPIBus
from st7789 import ST7789

import eventsys

try:
    from eventsys.keys import Keys
except ImportError:
    from keys import Keys

display_bus = SPIBus(
    id=0,
    baudrate=24_000_000,
    sck=4,
    mosi=5,
    miso=7,
    dc=29,
    cs=30,
    reset=31,
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
    cp={
        "width": 240,
        "height": 240,
        "rotation": 0,
        "colstart": 0,
        "rowstart": 80,
        "bgr": False,
        "reverse_bytes_in_word": True,
    },
)

# BUTTON_A=P1.02 → 34, BUTTON_B=P1.10 → 42 (nRF MP pin ids)
keypad = GPIOButtons(
    {
        "a": (Pin(34, Pin.IN, Pin.PULL_UP), Keys.K_a),
        "b": (Pin(42, Pin.IN, Pin.PULL_UP), Keys.K_b),
    }
)

# Sensors + STEMMA on P0.24/P0.25
i2c = I2C(0, sda=Pin(24), scl=Pin(25), freq=400_000)

runtime = eventsys.Runtime(display=display_drv)
runtime.add_keypad(read=keypad.read)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

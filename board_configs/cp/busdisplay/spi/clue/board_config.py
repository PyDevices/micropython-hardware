"""Adafruit CLUE (built-in ST7789) — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from keypad_gpio import GPIOButtons
from st7789 import ST7789

import eventsys

try:
    from eventsys.keys import Keys
except ImportError:
    from keys import Keys

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
    rotation=0,
    colstart=0,
    rowstart=80,
    bgr=False,
    reverse_bytes_in_word=True,
)

keypad = GPIOButtons(
    {
        "a": (board.BUTTON_A, Keys.K_a),
        "b": (board.BUTTON_B, Keys.K_b),
    }
)

runtime = eventsys.Runtime(display=display_drv)
runtime.add_keypad(read=keypad.read)

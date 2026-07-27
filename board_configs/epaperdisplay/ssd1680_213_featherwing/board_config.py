"""SSD1680 2.13" E-Ink FeatherWing — MicroPython (Feather SPI pinout)"""

from machine import SPI, Pin
from spibus import SPIBus
from ssd1680 import SSD1680

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=4_000_000,
    sck=18,
    mosi=19,
    miso=-1,
    command=9,
    chip_select=10,
    reset=6,
)
_epaper = SSD1680(
    display_bus,
    width=250,
    height=122,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=250, height=122, color_depth=1)

runtime = None

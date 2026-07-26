"""M5Stack Tab5 (ST7123 TDDI) - MicroPython"""

import time

from machine import I2C, Pin
from pi4ioe5v import tab5_init_lcd_reset
from st7123 import ST7123
from tab5_st7123_init import TAB5_ST7123_INIT

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from mipidsi import Bus, Display
except ImportError as exc:
    raise NotImplementedError("MIPI DSI requires displayif mipidsi cmod (esp32p4 port)") from exc

I2C_SCL = 32
I2C_SDA = 31
LCD_BACKLIGHT = 22
TOUCH_INT = 23

i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400_000)
# Panel reset / backlight owned by board_config (not mipidsi.Display).
tab5_init_lcd_reset(i2c)
time.sleep_ms(100)
lcd_backlight = Pin(LCD_BACKLIGHT, Pin.OUT, value=0)

touch = ST7123(
    i2c,
    irq_pin=Pin(TOUCH_INT),
    width=720,
    height=1_280,
)

display_bus = Bus(frequency=965_000_000, num_lanes=2)

fb = Display(
    display_bus,
    init_sequence=TAB5_ST7123_INIT,
    width=720,
    height=1_280,
    color_depth=16,
    pixel_clock_frequency=70_000_000,
    hsync_pulse_width=2,
    hsync_front_porch=40,
    hsync_back_porch=40,
    vsync_pulse_width=2,
    vsync_front_porch=220,
    vsync_back_porch=8,
)
lcd_backlight.value(1)


touch_rotation_table = (0, 0, 0, 0)

display_drv = FBDisplay(fb)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch.read_points,
    touch_rotation_table=touch_rotation_table,
)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

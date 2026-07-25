"""Lazy constructors for SparkFun IoT RedBoard RP2350. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"sdcard", "led", "i2c", "wlan", "ble"})

_SD_MISO = 8
_SD_CS = 9
_SD_SCK = 10
_SD_MOSI = 11


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def sdcard():
    """Onboard µSD on SPI1 (GPIO8–11)."""
    from machine import Pin, SPI

    from sdcard import SDCard

    spi = SPI(
        1,
        baudrate=1_000_000,
        polarity=0,
        phase=0,
        sck=Pin(_SD_SCK),
        mosi=Pin(_SD_MOSI),
        miso=Pin(_SD_MISO),
    )
    return SDCard(spi, Pin(_SD_CS, Pin.OUT, value=1))


def led():
    """Blue STAT LED on GPIO25."""
    from machine import Pin

    return Pin(25, Pin.OUT, value=0)


def i2c():
    """Qwiic / R3 I2C0 (GPIO4 SDA, GPIO5 SCL)."""
    from machine import I2C, Pin

    return I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)


def wlan():
    """RM2 CYW43 (same pin contract as Pico W / Pico 2 W)."""
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()

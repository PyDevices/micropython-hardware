"""Lazy constructors for PyGamer non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"pixels", "accelerometer", "sdcard", "battery", "audio", "i2c"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def pixels():
    """5× NeoPixel (PA15)."""
    from machine import Pin
    from neopixel import NeoPixel

    try:
        pin = Pin("NEOPIXEL")
    except ValueError:
        pin = Pin(15)
    return NeoPixel(pin, 5)


def accelerometer():
    """Onboard LIS3DH."""
    import board_config as bc
    from lis3dh import LIS3DH

    for addr in (0x18, 0x19):
        try:
            return LIS3DH(bc.i2c, address=addr)
        except OSError:
            continue
    raise OSError("LIS3DH not found on board I2C")


def sdcard():
    """microSD CS=PA14; share display SPI bus pins when SoftSPI is required."""
    from machine import Pin, SoftSPI

    from sdcard import SDCard

    try:
        cs = Pin("SD_CS", Pin.OUT, value=1)
    except ValueError:
        cs = Pin(14, Pin.OUT, value=1)
    spi = SoftSPI(
        baudrate=1_000_000,
        sck=Pin(13),
        mosi=Pin(11),
        miso=Pin(12),
    )
    return SDCard(spi, cs)


def battery():
    """Lipo monitor when firmware exposes A6 / BATTERY."""
    from battery_adc import BatteryADC

    try:
        return BatteryADC("BATTERY", scale=2.0)
    except (ValueError, TypeError):
        return BatteryADC(6, scale=2.0)


def audio():
    from machine import Pin, PWM

    try:
        Pin("SPEAKER_ENABLE", Pin.OUT, value=1)
        return PWM(Pin("SPEAKER"), freq=440, duty=0)
    except ValueError:
        Pin(27, Pin.OUT, value=1)
        return PWM(Pin(2), freq=440, duty=0)


def i2c():
    import board_config as bc

    return bc.i2c

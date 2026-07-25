"""Lazy constructors for CLUE non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset(
    {
        "accelerometer",
        "gyroscope",
        "magnetometer",
        "temperature",
        "humidity",
        "pressure",
        "microphone",
        "pixels",
        "led",
        "i2c",
        "ble",
    }
)

_bmp = None


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def _bmp280():
    global _bmp
    if _bmp is not None:
        return _bmp
    import board_config as bc
    from bmp280 import BMP280

    for addr in (0x77, 0x76):
        try:
            _bmp = BMP280(bc.i2c, addr=addr)
            return _bmp
        except OSError:
            continue
    raise OSError("BMP280 not found on CLUE I2C")


def accelerometer():
    raise NotImplementedError("CLUE LSM6DS33 driver not vendored yet")


def gyroscope():
    raise NotImplementedError("CLUE LSM6DS33 driver not vendored yet")


def magnetometer():
    raise NotImplementedError("CLUE LIS3MDL driver not vendored yet")


def temperature():
    """BMP280 temperature (SHT humidity sensor TBD)."""
    return _bmp280()


def humidity():
    raise NotImplementedError("CLUE SHT30/humidity driver not vendored yet")


def pressure():
    return _bmp280()


def microphone():
    """PDM mic pins P0.00/P0.01 — needs PDM/I2S firmware support."""
    raise NotImplementedError("CLUE PDM microphone needs port PDM/I2S wiring")


def pixels():
    """Single NeoPixel (P0.16)."""
    from machine import Pin
    from neopixel import NeoPixel

    return NeoPixel(Pin(16), 1)


def led():
    """White LED array (P0.10)."""
    from machine import Pin

    return Pin(10, Pin.OUT, value=0)


def i2c():
    import board_config as bc

    return bc.i2c


def ble():
    import bluetooth

    return bluetooth.BLE()

"""Lazy constructors for PyBadge non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"pixels", "accelerometer", "audio", "i2c"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def pixels():
    """5× NeoPixel strip (PA15)."""
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


def audio():
    """Speaker DAC + enable."""
    from machine import Pin, PWM

    try:
        Pin("SPEAKER_ENABLE", Pin.OUT, value=1)
        return PWM(Pin("SPEAKER"), freq=440, duty=0)
    except ValueError:
        Pin(27, Pin.OUT, value=1)
        return PWM(Pin(2), freq=440, duty=0)


def i2c():
    """STEMMA / sensor I2C — re-export UI-shared bus."""
    import board_config as bc

    return bc.i2c

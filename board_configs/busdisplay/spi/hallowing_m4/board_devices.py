"""Lazy constructors for HalloWing M4 non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"pixels", "accelerometer", "audio_out", "i2c"})

from audiodev.pwm_tone import PWMToneOutput

_i2c = None


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def i2c():
    global _i2c
    if _i2c is not None:
        return _i2c
    from machine import I2C, Pin

    try:
        _i2c = I2C(1, sda=Pin("SDA"), scl=Pin("SCL"), freq=400_000)
    except ValueError:
        _i2c = I2C(1, sda=Pin(12), scl=Pin(13), freq=400_000)
    return _i2c


def pixels():
    from machine import Pin
    from neopixel import NeoPixel

    try:
        pin = Pin("NEOPIXEL")
    except ValueError:
        pin = Pin(8)
    return NeoPixel(pin, 4)


def accelerometer():
    from lis3dh import LIS3DH

    bus = i2c()
    for addr in (0x18, 0x19):
        try:
            return LIS3DH(bus, address=addr)
        except OSError:
            continue
    raise OSError("LIS3DH not found on HalloWing I2C")


def audio_out():
    from machine import Pin, PWM

    try:
        enable = Pin("SPEAKER_ENABLE", Pin.OUT, value=0)
        speaker = Pin("SPEAKER")
    except ValueError:
        enable = None
        speaker = Pin(2)
    power = None if enable is None else lambda value: enable.value(value)
    return PWMToneOutput(lambda: PWM(speaker, freq=440, duty=0), power=power)

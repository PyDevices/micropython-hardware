"""Lazy constructors for PyBadge non-UI devices. PERIPHERALS = lazy roles only."""
import boarddev
import sys

PERIPHERALS = frozenset({"pixels", "accelerometer", "audio_out", "i2c"})

from audiodev.pwm_tone import PWMToneOutput


def load_peripherals(ns):
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


def audio_out():
    """Speaker DAC + enable."""
    from machine import Pin, PWM

    try:
        enable = Pin("SPEAKER_ENABLE", Pin.OUT, value=0)
        speaker = Pin("SPEAKER")
    except ValueError:
        enable = Pin(27, Pin.OUT, value=0)
        speaker = Pin(2)
    return PWMToneOutput(
        lambda: PWM(speaker, freq=440, duty=0),
        power=lambda value: enable.value(value),
    )


def i2c():
    """STEMMA / sensor I2C — re-export UI-shared bus."""
    import board_config as bc

    return bc.i2c

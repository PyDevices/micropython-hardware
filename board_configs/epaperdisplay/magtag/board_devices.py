"""Lazy constructors for MagTag non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"pixels", "audio_out", "i2c", "wlan"})

from audiodev import ToneOutput


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def pixels():
    """4× NeoPixel (GPIO1); enable power (GPIO21 active-low)."""
    from machine import Pin
    from neopixel import NeoPixel

    Pin(21, Pin.OUT, value=0)  # NEOPIXEL_POWER inverted: low = on
    return NeoPixel(Pin(1), 4)


def audio_out():
    """Speaker on GPIO17 with enable GPIO16."""
    from machine import Pin, PWM

    enable = Pin(16, Pin.OUT, value=0)
    return ToneOutput(
        lambda: PWM(Pin(17), freq=440, duty=0),
        power=lambda value: enable.value(value),
    )


def i2c():
    """STEMMA QT (SDA=33, SCL=34)."""
    from machine import I2C, Pin

    return I2C(0, sda=Pin(33), scl=Pin(34), freq=400_000)


def wlan():
    import network

    return network.WLAN(network.STA_IF)

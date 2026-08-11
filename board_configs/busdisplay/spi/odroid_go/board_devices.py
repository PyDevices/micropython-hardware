"""Lazy constructors for ODROID-GO non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"battery", "sdcard", "audio_out", "wlan"})

from audiodev.pwm_tone import PWMToneOutput


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def battery():
    from battery_adc import BatteryADC

    return BatteryADC(36, scale=2.0)


def sdcard():
    """TF card on VSPI CS=GPIO22 (shared SPI pins with display)."""
    from machine import Pin, SoftSPI

    from sdcard import SDCard

    spi = SoftSPI(baudrate=1_000_000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
    return SDCard(spi, Pin(22, Pin.OUT, value=1))


def audio_out():
    from machine import Pin, PWM

    return PWMToneOutput(lambda: PWM(Pin(26), freq=440, duty=0))


def wlan():
    import network

    return network.WLAN(network.STA_IF)

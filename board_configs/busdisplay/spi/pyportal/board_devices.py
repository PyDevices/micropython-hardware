"""Lazy constructors for PyPortal non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"sdcard", "radio", "audio", "i2c", "wlan"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def sdcard():
    """microSD on SPI (CS=PB30 when named; else pin 30)."""
    from machine import Pin, SoftSPI

    from sdcard import SDCard

    try:
        cs = Pin("SD_CS", Pin.OUT, value=1)
    except ValueError:
        cs = Pin(30, Pin.OUT, value=1)
    spi = SoftSPI(
        baudrate=1_000_000,
        sck=Pin(13),
        mosi=Pin(12),
        miso=Pin(14),
    )
    return SDCard(spi, cs)


def radio():
    """ESP32 AirLift co-processor — same NIC as ``wlan`` when nina-fw is linked."""
    return wlan()


def audio():
    from machine import Pin, PWM

    try:
        Pin("SPEAKER_ENABLE", Pin.OUT, value=1)
        return PWM(Pin("SPEAKER"), freq=440, duty=0)
    except ValueError:
        return PWM(Pin(2), freq=440, duty=0)


def i2c():
    """STEMMA / touch I2C — re-export UI-shared bus."""
    import board_config as bc

    return bc.i2c


def wlan():
    """AirLift / board default station interface."""
    import network

    return network.WLAN(network.STA_IF)

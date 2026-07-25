"""Lazy constructors for T-Dongle-S3 non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"pixels", "wlan", "ble"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def pixels():
    """APA102 (DotStar) on LilyGO T-Dongle-S3 (CLK=39, DATA=40)."""
    from machine import Pin, SoftSPI

    from dotstar import DotStar

    spi = SoftSPI(baudrate=1_000_000, sck=Pin(39), mosi=Pin(40), miso=Pin(38))
    return DotStar(spi, 1, auto_write=True)


def wlan():
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()

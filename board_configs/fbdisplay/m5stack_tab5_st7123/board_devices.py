"""Lazy constructors for M5Stack Tab5 (ST7123). DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"microphone", "audio", "sdcard", "camera", "i2c", "wlan", "ble"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def i2c():
    import board_config as bc

    return bc.i2c


def microphone():
    raise NotImplementedError("Tab5 microphone needs codec/I2S bring-up")


def audio():
    raise NotImplementedError("Tab5 audio needs codec/I2S bring-up")


def sdcard():
    from machine import SDCard

    return SDCard()


def camera():
    raise NotImplementedError("Tab5 camera needs native CSI support")


def wlan():
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()

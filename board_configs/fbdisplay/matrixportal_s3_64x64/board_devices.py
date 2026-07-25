"""Lazy constructors for MatrixPortal S3 non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"accelerometer", "i2c", "wlan", "ble"})

_i2c = None


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def i2c():
    global _i2c
    if _i2c is not None:
        return _i2c
    from machine import I2C, Pin

    # STEMMA QT on MatrixPortal S3
    _i2c = I2C(0, sda=Pin(16), scl=Pin(15), freq=400_000)
    return _i2c


def accelerometer():
    from lis3dh import LIS3DH

    bus = i2c()
    for addr in (0x19, 0x18):
        try:
            return LIS3DH(bus, address=addr)
        except OSError:
            continue
    raise OSError("LIS3DH not found on MatrixPortal S3 I2C")


def wlan():
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()

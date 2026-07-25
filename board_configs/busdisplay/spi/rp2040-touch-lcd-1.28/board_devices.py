"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({'accelerometer', 'gyroscope', 'battery'})

def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

def accelerometer():
    """QMI8658 on Waveshare RP2040-Touch-LCD-1.28 (I2C1 GP6/GP7)."""
    from machine import I2C, Pin

    try:
        i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=100_000, timeout=1000)
    except TypeError:
        i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=100_000)
    try:
        from qmi8658 import QMI8658
    except ImportError as exc:
        raise NotImplementedError("mip-install qmi8658 driver for accelerometer") from exc
    return QMI8658(i2c)

def gyroscope():
    """Same QMI8658 instance role as accelerometer (6-axis)."""
    return accelerometer()

def battery():
    raise NotImplementedError("battery factory not wired for this proof board yet")


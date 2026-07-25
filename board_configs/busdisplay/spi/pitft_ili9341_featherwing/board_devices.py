"""Lazy constructors for PiTFT FeatherWing. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"i2c"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def i2c():
    """Host Feather STEMMA / I2C (pin names when firmware exposes them)."""
    from machine import I2C, Pin

    try:
        return I2C(0, sda=Pin("SDA"), scl=Pin("SCL"), freq=400_000)
    except ValueError:
        return I2C(0, sda=Pin(2), scl=Pin(3), freq=400_000)

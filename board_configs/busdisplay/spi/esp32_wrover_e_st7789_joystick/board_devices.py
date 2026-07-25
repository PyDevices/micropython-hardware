"""Lazy constructors for ESP32-WROVER-E joystick board. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"wlan"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def wlan():
    import network

    return network.WLAN(network.STA_IF)

"""Lazy constructors for Pico 2 W + DVI Sock/PiCowbell. PERIPHERALS = lazy roles only."""
import boarddev
import sys

PERIPHERALS = frozenset({"wlan", "ble"})


def load_peripherals(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def wlan():
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()

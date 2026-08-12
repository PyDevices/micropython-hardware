"""Lazy constructors for T-Display-S3 non-UI devices. PERIPHERALS = lazy roles only."""
import boarddev
import sys

PERIPHERALS = frozenset({"battery", "wlan", "ble"})


def load_peripherals(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def battery():
    from battery_adc import BatteryADC

    return BatteryADC(4, scale=2.0)


def wlan():
    import network

    return network.WLAN(network.STA_IF)


def ble():
    import bluetooth

    return bluetooth.BLE()

"""Lazy constructors for T-QT Pro non-UI devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({"battery", "wlan", "ble"})


def setup_devices(ns):
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

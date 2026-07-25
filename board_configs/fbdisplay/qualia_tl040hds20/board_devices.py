"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({'wlan', 'ble'})

def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

def wlan():
    import network
    return network.WLAN(network.STA_IF)

def ble():
    import bluetooth
    return bluetooth.BLE()


"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({'sdcard', 'battery', 'wlan', 'ble'})

def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

def sdcard():
    raise NotImplementedError("sdcard factory not wired for this proof board yet")

def battery():
    raise NotImplementedError("battery factory not wired for this proof board yet")

def wlan():
    import network
    return network.WLAN(network.STA_IF)

def ble():
    import bluetooth
    return bluetooth.BLE()


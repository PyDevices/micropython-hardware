"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({'sdcard', 'can', 'rs485', 'usb_device', 'wlan', 'ble'})

def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

def sdcard():
    raise NotImplementedError("sdcard factory not wired for this proof board yet")

def can():
    raise NotImplementedError("can factory not wired for this proof board yet")

def rs485():
    raise NotImplementedError("rs485 factory not wired for this proof board yet")

def usb_device():
    from machine import USBDevice
    return USBDevice()

def wlan():
    import network
    return network.WLAN(network.STA_IF)

def ble():
    import bluetooth
    return bluetooth.BLE()


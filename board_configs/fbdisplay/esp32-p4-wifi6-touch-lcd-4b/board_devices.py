"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({'audio', 'microphone', 'sdcard', 'camera', 'ethernet', 'radio', 'wlan', 'ble', 'usb_device'})

def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

def audio():
    raise NotImplementedError("audio endpoint factory not wired for this proof board yet")

def microphone():
    raise NotImplementedError("microphone factory not wired for this proof board yet")

def sdcard():
    raise NotImplementedError("sdcard factory not wired for this proof board yet")

def camera():
    raise NotImplementedError("camera factory not wired for this proof board yet")

def ethernet():
    # Board-specific PHY bring-up belongs here when wired.
    raise NotImplementedError("ethernet factory not wired for this proof board yet")

def radio():
    raise NotImplementedError("radio co-processor factory not wired for this proof board yet")

def wlan():
    import network
    return network.WLAN(network.STA_IF)

def ble():
    import bluetooth
    return bluetooth.BLE()

def usb_device():
    from machine import USBDevice
    return USBDevice()


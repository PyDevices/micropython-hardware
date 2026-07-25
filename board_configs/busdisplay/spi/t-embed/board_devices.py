"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({'pixels', 'audio', 'microphone', 'sdcard', 'battery', 'i2c', 'wlan', 'ble'})

def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

def pixels():
    raise NotImplementedError("pixels factory not wired for this proof board yet")

def audio():
    raise NotImplementedError("audio endpoint factory not wired for this proof board yet")

def microphone():
    raise NotImplementedError("microphone factory not wired for this proof board yet")

def sdcard():
    raise NotImplementedError("sdcard factory not wired for this proof board yet")

def battery():
    raise NotImplementedError("battery factory not wired for this proof board yet")

def i2c():
    """T-Embed Qwiic / expansion I2C."""
    from machine import I2C, Pin
    return I2C(0, sda=Pin(8), scl=Pin(9), freq=400_000)

def wlan():
    import network
    return network.WLAN(network.STA_IF)

def ble():
    import bluetooth
    return bluetooth.BLE()


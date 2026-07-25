"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({'sdcard', 'i2c', 'wlan', 'ble'})

def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

def sdcard():
    """T-HMI TF card (SDMMC) — pins per LilyGO."""
    from machine import SDCard
    return SDCard(slot=1)  # board firmware mapping; adjust if needed

def i2c():
    """Primary Grove I2C (not the touch SPI)."""
    from machine import I2C, Pin
    return I2C(0, sda=Pin(17), scl=Pin(18), freq=400_000)

def wlan():
    import network
    return network.WLAN(network.STA_IF)

def ble():
    import bluetooth
    return bluetooth.BLE()


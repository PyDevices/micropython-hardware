"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({'pixels', 'led', 'sdcard', 'radio', 'wlan', 'i2c'})

def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

def pixels():
    raise NotImplementedError("pixels factory not wired for this proof board yet")

def led():
    raise NotImplementedError("led factory not wired for this proof board yet")

def sdcard():
    raise NotImplementedError("sdcard factory not wired for this proof board yet")

def radio():
    raise NotImplementedError("radio co-processor factory not wired for this proof board yet")

def wlan():
    # AirLift on shield when present; else ESP32 co-proc radio path.
    raise NotImplementedError("wlan via radio/AirLift not wired in this proof yet")

def i2c():
    """Shield / STEMMA I2C — re-export UI bus when already constructed."""
    import board_config as bc
    return bc.i2c


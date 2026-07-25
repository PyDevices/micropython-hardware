"""Lazy constructors for contract_proof board devices. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset({'led', 'sdcard', 'ethernet'})

def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

def led():
    raise NotImplementedError("led factory not wired for this proof board yet")

def sdcard():
    raise NotImplementedError("sdcard factory not wired for this proof board yet")

def ethernet():
    # Board-specific PHY bring-up belongs here when wired.
    raise NotImplementedError("ethernet factory not wired for this proof board yet")


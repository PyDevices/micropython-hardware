"""Lazy constructors for Teensy 4.1 RGB matrix wing. DEVICES = lazy roles only."""
import boarddev
import sys

DEVICES = frozenset()


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

"""Lazy constructors for Pico 2 + DVI Sock/PiCowbell. DEVICES = lazy roles only."""
import boarddev
import sys

# No onboard wireless (use pico2w_dvi_sock_640x480 for Pico 2 W).
DEVICES = frozenset()


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])

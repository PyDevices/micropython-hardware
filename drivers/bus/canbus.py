# SPDX-FileCopyrightText: 2026 Brad Barnett / PyDevices
#
# SPDX-License-Identifier: MIT
"""CAN / TWAI factory helper.

Stock MicroPython ESP32 builds do not yet expose ``machine.CAN``. When the
port gains it (or a firmware ships a ``CAN`` type), this helper constructs it.
Until then, ``open()`` raises ``NotImplementedError`` with a clear message.
"""


def open(tx, rx, *, baudrate=500_000, mode=None, extframe=False):
    """Return a CAN controller for the given TX/RX pins."""
    try:
        from machine import CAN
    except ImportError as exc:
        raise NotImplementedError(
            "machine.CAN / TWAI is not available in this firmware "
            "(needed for ESP32 CAN transceiver boards)"
        ) from exc

    kwargs = {"tx": tx, "rx": rx, "baudrate": baudrate, "extframe": extframe}
    if mode is not None:
        kwargs["mode"] = mode
    try:
        return CAN(0, **kwargs)
    except TypeError:
        # Alternate constructor shapes across ports.
        return CAN(0, mode if mode is not None else 0, baudrate, (tx, rx))

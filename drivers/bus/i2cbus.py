# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
i2cbus — I2C display bus for SSD1306-class OLED panels (MicroPython).

Implements the ``send(command, data)`` contract used by ``BusDisplay``.
Signature matches displayif ``I2CBus`` / CircuitPython ``I2CDisplayBus``.
"""

from time import sleep_us

from machine import Pin
from micropython import const

_CO_DATA = const(0x40)
_CO_CMD = const(0x00)


def _pin_unset(pin) -> bool:
    return pin is None or pin == -1


class I2CBus:
    """
    I2C bus for displayio-style OLED controllers.

    Args:
        i2c_bus: ``machine.I2C`` instance (positional).
        device_address (int): I2C device address (required keyword).
        reset: Optional reset pin (int, name str, or Pin).
    """

    def __init__(self, i2c_bus, *, device_address, reset=None):
        self._i2c = i2c_bus
        self._address = device_address
        self._reset = None if _pin_unset(reset) else Pin(reset, Pin.OUT, value=1)
        if self._reset is not None:
            # Match CircuitPython I2CDisplayBus: pulse reset on construct.
            self._reset.value(0)
            sleep_us(4)
            self._reset.value(1)

    def reset(self) -> None:
        """Hardware reset pulse when ``reset`` pin was provided."""
        if self._reset is None:
            raise RuntimeError("No reset pin defined")
        self._reset.value(0)
        sleep_us(4)
        self._reset.value(1)

    def send(self, command, data=None):
        if data is None:
            data = b""
        if isinstance(command, int):
            self._i2c.writeto(self._address, bytes([_CO_CMD, command]) + bytes(data))
        else:
            self._i2c.writeto(self._address, bytes([_CO_CMD]) + bytes(command) + bytes(data))

    def send_data(self, data):
        self._i2c.writeto(self._address, bytes([_CO_DATA]) + bytes(data))

    def deinit(self) -> None:
        pass

    def __del__(self) -> None:
        self.deinit()

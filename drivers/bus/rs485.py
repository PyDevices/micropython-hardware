# SPDX-FileCopyrightText: 2026 Brad Barnett / PyDevices
#
# SPDX-License-Identifier: MIT
"""RS485 as a UART (+ optional driver-enable pin)."""

from machine import UART, Pin


class RS485:
    """UART wrapper for SP3485-style automatic or DE-pin half-duplex links.

    Boards with hardware auto-direction (Waveshare S3 Touch LCD) omit ``de``.
    """

    def __init__(self, uart_id, *, tx, rx, baudrate=115200, de=None, bits=8, parity=None, stop=1):
        self.uart = UART(
            uart_id,
            baudrate=baudrate,
            bits=bits,
            parity=parity,
            stop=stop,
            tx=Pin(tx) if not isinstance(tx, Pin) else tx,
            rx=Pin(rx) if not isinstance(rx, Pin) else rx,
        )
        self._de = None
        if de is not None:
            self._de = de if isinstance(de, Pin) else Pin(de, Pin.OUT, value=0)

    def write(self, buf):
        if self._de is not None:
            self._de(1)
        n = self.uart.write(buf)
        if self._de is not None:
            try:
                self.uart.flush()
            except AttributeError:
                pass
            self._de(0)
        return n

    def read(self, n=-1):
        return self.uart.read(n)

    def readline(self):
        return self.uart.readline()

    def any(self):
        return self.uart.any()

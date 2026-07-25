# SPDX-FileCopyrightText: 2026 Brad Barnett / PyDevices
#
# SPDX-License-Identifier: MIT
"""Minimal ES7210 ADC codec init (I2C) for I2S microphone paths.

Register sequence distilled from Espressif / LilyGO ES7210 bring-up used on
T-Embed. Enough to power the ADCs so ``machine.I2S`` RX can capture samples.
"""

import time

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


I2C_ADDR = const(0x40)

_RESET = const(0x00)
_CLOCK_OFF = const(0x01)
_MAIN_CLK = const(0x02)
_MASTER_CLK = const(0x03)
_MRC_ANALOG = const(0x06)
_ANALOG = const(0x07)
_MIC1_GAIN = const(0x43)
_MIC2_GAIN = const(0x44)
_MIC3_GAIN = const(0x45)
_MIC4_GAIN = const(0x46)
_MODE = const(0x08)
_SDP12 = const(0x11)
_SDP34 = const(0x12)
_ADC_CTRL = const(0x40)


class ES7210:
    """Power up ES7210 ADCs for I2S slave capture."""

    def __init__(self, i2c, address=I2C_ADDR, *, gain=0x1A):
        self._i2c = i2c
        self._addr = address
        self._init(gain)

    def _wr(self, reg, val):
        self._i2c.writeto_mem(self._addr, reg, bytes((val & 0xFF,)))

    def _init(self, gain):
        self._wr(_RESET, 0xFF)
        time.sleep_ms(10)
        self._wr(_RESET, 0x41)
        self._wr(_CLOCK_OFF, 0x1F)
        self._wr(_MAIN_CLK, 0xC1)
        self._wr(_MASTER_CLK, 0x04)
        self._wr(_MRC_ANALOG, 0x00)
        self._wr(_ANALOG, 0x00)
        self._wr(_MODE, 0x10)
        # 16-bit I2S, dual mic on channels 1/2
        self._wr(_SDP12, 0x60)
        self._wr(_SDP34, 0x00)
        self._wr(_MIC1_GAIN, gain)
        self._wr(_MIC2_GAIN, gain)
        self._wr(_MIC3_GAIN, 0x00)
        self._wr(_MIC4_GAIN, 0x00)
        self._wr(_ADC_CTRL, 0xC0)
        self._wr(_CLOCK_OFF, 0x00)
        time.sleep_ms(20)

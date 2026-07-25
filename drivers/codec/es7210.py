# SPDX-FileCopyrightText: 2026 Brad Barnett / PyDevices
#
# SPDX-License-Identifier: MIT
"""Minimal ES7210 ADC codec init (I2C) for I2S microphone paths.

``profile="default"`` matches Espressif / LilyGO T-Embed bring-up.
``profile="m5"`` matches M5Unified CoreS3 / Tab5 mic enable sequences.
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

# M5Unified CoreS3 / Tab5 mic enable (after RESET 0xFF)
_M5_INIT = (
    (0x00, 0x41),
    (0x01, 0x1F),
    (0x06, 0x00),
    (0x07, 0x20),
    (0x08, 0x10),
    (0x09, 0x30),
    (0x0A, 0x30),
    (0x20, 0x0A),
    (0x21, 0x2A),
    (0x22, 0x0A),
    (0x23, 0x2A),
    (0x02, 0xC1),
    (0x04, 0x01),
    (0x05, 0x00),
    (0x11, 0x60),
    (0x40, 0x42),
    (0x41, 0x70),
    (0x42, 0x70),
    (0x43, 0x1B),
    (0x44, 0x1B),
    (0x45, 0x00),
    (0x46, 0x00),
    (0x47, 0x00),
    (0x48, 0x00),
    (0x49, 0x00),
    (0x4A, 0x00),
    (0x4B, 0x00),
    (0x4C, 0xFF),
    (0x01, 0x14),
)


class ES7210:
    """Power up ES7210 ADCs for I2S slave capture."""

    def __init__(self, i2c, address=I2C_ADDR, *, gain=0x1A, profile="default"):
        self._i2c = i2c
        self._addr = address
        if profile == "m5":
            self._init_m5()
        elif profile == "default":
            self._init_default(gain)
        else:
            raise ValueError("unknown ES7210 profile %r" % (profile,))

    def _wr(self, reg, val):
        self._i2c.writeto_mem(self._addr, reg, bytes((val & 0xFF,)))

    def _init_default(self, gain):
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

    def _init_m5(self):
        self._wr(_RESET, 0xFF)
        time.sleep_ms(10)
        for reg, val in _M5_INIT:
            self._wr(reg, val)
        time.sleep_ms(20)

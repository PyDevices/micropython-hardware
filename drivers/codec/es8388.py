# SPDX-FileCopyrightText: 2026 Brad Barnett / PyDevices
#
# SPDX-License-Identifier: MIT
"""Minimal ES8388 DAC init (I2C) for I2S speaker paths.

Register sequence distilled from M5Unified Tab5
(``_speaker_enabled_cb_tab5``). Enough to unmute DAC + line outs so
``machine.I2S`` TX can play samples. ADC bring-up is left to a separate
codec (Tab5 uses ES7210 for mics).
"""

import time

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


I2C_ADDR = const(0x10)


def _sleep_ms(milliseconds):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(milliseconds)
    else:
        time.sleep(milliseconds / 1000)

# (reg, value) — Tab5 speaker enable bulk (DAC path)
_INIT = (
    (0x00, 0x80),  # RESET / CSM power on
    (0x00, 0x00),
    (0x00, 0x00),
    (0x00, 0x0E),
    (0x01, 0x00),
    (0x02, 0x0A),  # chip power up
    (0x03, 0xFF),  # ADC power down
    (0x04, 0x3C),  # DAC + LOUT/ROUT 1/2
    (0x05, 0x00),
    (0x06, 0x00),
    (0x07, 0x7C),  # VSEL
    (0x08, 0x00),  # I2S slave
    (0x17, 0x18),  # 16-bit I2S
    (0x18, 0x00),  # MCLK ratio 128
    (0x19, 0x20),  # DAC unmute
    (0x1A, 0x00),  # LDACVOL
    (0x1B, 0x00),  # RDACVOL
    (0x1C, 0x08),  # click-free power
    (0x1D, 0x00),
    (0x26, 0x00),  # DAC CTRL16
    (0x27, 0xB8),  # left mix
    (0x2A, 0xB8),  # right mix
    (0x2B, 0x08),  # ADC/DAC separate LRCK
    (0x2D, 0x00),
    (0x2E, 0x21),
    (0x2F, 0x21),
    (0x30, 0x21),
    (0x31, 0x21),
)


class ES8388:
    """Power up ES8388 DAC for I2S slave playback."""

    def __init__(self, i2c, address=I2C_ADDR):
        self._i2c = i2c
        self._addr = address
        self.volume = 100
        self.muted = False
        self.enabled = False
        self._init()

    def _wr(self, reg, val):
        self._i2c.writeto_mem(self._addr, reg, bytes((val & 0xFF,)))

    def _init(self):
        for reg, val in _INIT:
            self._wr(reg, val)
            if reg == 0x00 and val == 0x80:
                _sleep_ms(10)
        self.enabled = True

    def set_dac_volume(self, percent):
        """Set stereo DAC volume from -96 dB (0%) to 0 dB (100%)."""
        percent = max(0, min(100, int(percent)))
        attenuation = (100 - percent) * 0xC0 // 100
        self._wr(0x1A, attenuation)
        self._wr(0x1B, attenuation)
        self.volume = percent
        return percent

    def dac_mute(self, mute=True):
        """Mute both DAC analog outputs while retaining the signal path."""
        self._wr(0x19, 0x24 if mute else 0x20)
        self.muted = bool(mute)

    def enable_output(self, enable=True):
        enable = bool(enable)
        if enable:
            self._wr(0x04, 0x3C)
        else:
            self.dac_mute(True)
            self._wr(0x04, 0xC0)
        self.enabled = enable

    def close(self):
        self.enable_output(False)

    deinit = close

# SPDX-FileCopyrightText: 2026 Brad Barnett / PyDevices
#
# SPDX-License-Identifier: MIT
"""Minimal AW88298 smart amp init (I2C, 16-bit regs) for I2S TX.

Register sequence distilled from M5Unified CoreS3 speaker bring-up
(``_speaker_enabled_cb_cores3``). Values are written big-endian.
"""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


I2C_ADDR = const(0x36)
_AW9523_ADDR = const(0x58)
_AW9523_P0 = const(0x02)
_AW9523_SPK_BIT = const(0x04)

# Sample-rate index table from M5Unified (kHz buckets via (rate+1102)//2205)
_RATE_TBL = (4, 5, 6, 8, 10, 11, 15, 20, 22, 44)


class AW88298:
    """Power up AW88298 for I2S slave playback."""

    def __init__(self, i2c, address=I2C_ADDR, *, sample_rate=16000, enable_aw9523=True):
        self._i2c = i2c
        self._addr = address
        if enable_aw9523:
            self.enable_cores3_amp(True)
        self._init(sample_rate)

    def _wr16(self, reg, value):
        # AW88298 expects big-endian 16-bit register values
        self._i2c.writeto_mem(self._addr, reg, bytes(((value >> 8) & 0xFF, value & 0xFF)))

    def _init(self, sample_rate):
        rate = (sample_rate + 1102) // 2205
        idx = 0
        while idx < len(_RATE_TBL) - 1 and rate > _RATE_TBL[idx]:
            idx += 1
        reg06 = idx | 0x14C0  # I2SBCK mode 16*2
        self._wr16(0x61, 0x0673)  # boost mode disabled
        self._wr16(0x04, 0x4040)  # I2SEN=1 AMPPD=0 PWDN=0
        self._wr16(0x05, 0x0008)  # HMUTE=0
        self._wr16(0x06, reg06)
        self._wr16(0x0C, 0x0064)  # full volume

    def enable_cores3_amp(self, enable=True):
        """Toggle CoreS3 AW9523 P0.2 speaker path (no-op if expander absent)."""
        try:
            cur = self._i2c.readfrom_mem(_AW9523_ADDR, _AW9523_P0, 1)[0]
            if enable:
                cur |= _AW9523_SPK_BIT
            else:
                cur &= ~_AW9523_SPK_BIT
            self._i2c.writeto_mem(_AW9523_ADDR, _AW9523_P0, bytes((cur,)))
        except OSError:
            pass

    def shutdown(self):
        """Disable I2S path on the amp (keeps chip powered)."""
        self._wr16(0x04, 0x4000)
        self.enable_cores3_amp(False)

# SPDX-FileCopyrightText: 2026 PyDevices
# SPDX-License-Identifier: MIT
"""Minimal I2C driver for ST LIS3DH (PyGamer / PyBadge / Feather)."""

from micropython import const

_REG_WHO_AM_I = const(0x0F)
_REG_CTRL1 = const(0x20)
_REG_CTRL4 = const(0x23)
_REG_OUT_X_L = const(0x28)
_WHO_AM_I = const(0x33)
# CTRL1: 100 Hz, XYZ enable. CTRL4: high-res, ±4g
_CTRL1_100HZ_XYZ = const(0x57)
_CTRL4_HR_4G = const(0x88)
_SENS_4G = 0.000122  # g / LSB in high-res ±4g


class LIS3DH:
    """Return acceleration in g as ``(x, y, z)``."""

    def __init__(self, i2c, address=0x18):
        self._i2c = i2c
        self._addr = address
        who = self._read(_REG_WHO_AM_I, 1)[0]
        if who != _WHO_AM_I:
            raise OSError("LIS3DH WHO_AM_I {:#x} (expected {:#x})".format(who, _WHO_AM_I))
        self._write(_REG_CTRL1, bytes([_CTRL1_100HZ_XYZ]))
        self._write(_REG_CTRL4, bytes([_CTRL4_HR_4G]))

    def _read(self, reg, n):
        return self._i2c.readfrom_mem(self._addr, reg, n)

    def _write(self, reg, data):
        self._i2c.writeto_mem(self._addr, reg, data)

    @staticmethod
    def _s16(lo, hi):
        v = lo | (hi << 8)
        return v - 0x10000 if v & 0x8000 else v

    @property
    def acceleration(self):
        # Auto-increment OUT_X_L
        raw = self._read(_REG_OUT_X_L | 0x80, 6)
        x = self._s16(raw[0], raw[1])
        y = self._s16(raw[2], raw[3])
        z = self._s16(raw[4], raw[5])
        return (x * _SENS_4G, y * _SENS_4G, z * _SENS_4G)

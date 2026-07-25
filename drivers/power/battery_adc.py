# SPDX-FileCopyrightText: 2026 Brad Barnett / PyDevices
#
# SPDX-License-Identifier: MIT
"""Thin battery helper over ``machine.ADC`` + resistor divider."""

from machine import ADC, Pin


class BatteryADC:
    """Read pack voltage through a divider.

    ``voltage`` returns volts at the battery (ADC reading × ``scale``).
    Typical ESP32 divider is 1:1 (scale=2.0) from a mid-point tap.
    """

    def __init__(self, pin, *, scale=2.0, atten=None):
        self._scale = scale
        try:
            self._adc = ADC(Pin(pin))
        except TypeError:
            self._adc = ADC(pin)
        if atten is not None:
            try:
                self._adc.atten(atten)
            except (AttributeError, ValueError, TypeError):
                pass
        else:
            try:
                self._adc.atten(ADC.ATTN_11DB)
            except (AttributeError, ValueError, TypeError):
                pass

    def read_u16(self):
        return self._adc.read_u16()

    @property
    def voltage(self):
        """Battery voltage in volts."""
        try:
            return (self._adc.read_uv() / 1_000_000.0) * self._scale
        except AttributeError:
            return (self._adc.read_u16() / 65535.0) * 3.3 * self._scale

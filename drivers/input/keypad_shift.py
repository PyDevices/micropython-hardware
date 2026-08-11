# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""74HC165 shift-register keypad helper for PyBadge / PyGamer."""

import keys


def _as_out(pin):
    """Accept MP pin id / Pin, or CP DigitalInOut / Pin-like."""
    if hasattr(pin, "switch_to_output"):
        pin.switch_to_output()
        return pin
    try:
        from machine import Pin

        if isinstance(pin, int):
            return Pin(pin, Pin.OUT)
        if hasattr(pin, "init"):
            pin.init(Pin.OUT)
            return pin
    except ImportError:
        pass
    return pin


def _as_in(pin):
    if hasattr(pin, "switch_to_input"):
        try:
            import digitalio

            pin.switch_to_input(pull=digitalio.Pull.UP)
        except (ImportError, TypeError, ValueError):
            pin.switch_to_input()
        return pin
    try:
        from machine import Pin

        if isinstance(pin, int):
            return Pin(pin, Pin.IN, Pin.PULL_UP)
        if hasattr(pin, "init"):
            pin.init(Pin.IN, Pin.PULL_UP)
            return pin
    except ImportError:
        pass
    return pin


def _set_level(pin, level):
    if hasattr(pin, "value") and not callable(pin.value):
        pin.value = level
    else:
        pin.value(level)


def _get_level(pin):
    value = pin.value
    return value() if callable(value) else value


class ShiftRegisterButtons:
    """
    Read buttons wired to a 74HC165 shift register.

    Args:
        clock: Clock pin.
        latch: Latch pin.
        data: Serial data out pin.
        mapping: Dict of name -> (bit_index, key_code).
        key_count (int): Number of bits to clock out.
        value_when_pressed (bool): Raw bit value when pressed.
    """

    def __init__(
        self,
        clock,
        latch,
        data,
        mapping,
        *,
        key_count=8,
        value_when_pressed=True,
    ):
        self._clock = _as_out(clock)
        self._latch = _as_out(latch)
        self._data = _as_in(data)
        self._key_count = key_count
        self._value_when_pressed = value_when_pressed
        self._buttons = [(bit_index, key_code) for bit_index, key_code in mapping.values()]

    def _read_bits(self):
        _set_level(self._latch, 0)
        _set_level(self._latch, 1)
        _set_level(self._latch, 0)
        bits = []
        for _ in range(self._key_count):
            bits.append(_get_level(self._data))
            _set_level(self._clock, 1)
            _set_level(self._clock, 0)
        return bits

    def read(self):
        bits = self._read_bits()
        pressed = []
        for bit_index, key in self._buttons:
            if bits[bit_index] == self._value_when_pressed:
                pressed.append(key)
        return pressed


PYBADGE_BUTTON_MAP = {
    "a": (1, keys.K_a),
    "b": (0, keys.K_b),
    "c": (2, keys.K_c),
    "d": (3, keys.K_d),
}

# PyGamer / PyBadge LC shift-register layout (Adafruit): A/B + Start/Select.
PYGAMER_BUTTON_MAP = {
    "b": (0, keys.K_b),
    "a": (1, keys.K_a),
    "start": (2, keys.K_RETURN),
    "select": (3, keys.K_SPACE),
}

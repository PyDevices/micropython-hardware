# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""``BusDisplay`` init-sequence dispatch.

A display whose init sequence is never sent looks intermittently blank or
washed out and reports no error at all -- the panel simply runs on whatever
state it powered up in. That is what happened on a real GC9A01: the driver
declares its sequence as ``bytearray``, ``bytearray`` is not a subclass of
``bytes``, and the dispatch tested only for ``bytes``, so panel bring-up was
skipped silently. These tests pin the accepted types down and require the
unusable case to raise instead of passing quietly.
"""

import unittest

import _env  # noqa: F401

from displaydev.busdisplay import BusDisplay


class RecordingBus:
    """Captures (command, data) so a test can prove the sequence went out."""

    def __init__(self):
        self.sent = []

    def send(self, command, data=b"", **kwargs):
        self.sent.append((command, bytes(data)))


# SWRESET (no params), COLMOD 0x05, SLPOUT + 120ms delay, DISPON + 20ms delay.
_SEQUENCE = b"\x01\x00\x3a\x01\x05\x11\x80\x78\x29\x80\x14"
_COMMANDS = [0x01, 0x3A, 0x11, 0x29]


def _build(sequence):
    bus = RecordingBus()
    drv = BusDisplay(bus, sequence, width=8, height=8, quiet=True)
    return bus, drv


class TestBusDisplayInitDispatch(unittest.TestCase):
    def _assert_sequence_sent(self, bus):
        sent = [cmd for cmd, _ in bus.sent]
        for command in _COMMANDS:
            self.assertIn(command, sent, "init sequence was not sent")

    def test_bytes_sequence_is_sent(self):
        bus, _ = _build(_SEQUENCE)
        self._assert_sequence_sent(bus)

    def test_bytearray_sequence_is_sent(self):
        # The regression: bytearray is not an instance of bytes.
        self.assertFalse(isinstance(bytearray(b"x"), bytes))
        bus, _ = _build(bytearray(_SEQUENCE))
        self._assert_sequence_sent(bus)

    def test_memoryview_sequence_is_sent(self):
        bus, _ = _build(memoryview(_SEQUENCE))
        self._assert_sequence_sent(bus)

    def test_list_sequence_is_sent(self):
        bus, _ = _build([(0x01, b"", 0), (0x3A, b"\x05", 0), (0x11, b"", 120), (0x29, b"", 20)])
        self._assert_sequence_sent(bus)

    def test_panel_chosen_color_mode_is_not_overwritten(self):
        # The sequence sets COLMOD 0x05; the generic 16-bit value is 0x55.
        # Sending 0x55 afterwards drives the panel through a format it may not
        # recover from, so the init sequence has to win.
        bus, drv = _build(bytearray(_SEQUENCE))
        self.assertTrue(drv._init_set_color_mode)
        colmod = [data for cmd, data in bus.sent if cmd == 0x3A]
        self.assertEqual([b"\x05"], colmod)

    def test_color_mode_still_sent_when_sequence_omits_it(self):
        bus, drv = _build(b"\x01\x00")
        self.assertFalse(drv._init_set_color_mode)
        self.assertIn(b"\x55", [data for cmd, data in bus.sent if cmd == 0x3A])

    def test_unusable_sequence_raises_instead_of_passing_quietly(self):
        with self.assertRaises(TypeError):
            _build("not a buffer")


if __name__ == "__main__":
    unittest.main()

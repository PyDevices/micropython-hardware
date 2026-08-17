# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for JNDisplay and JNDevices input handling (mouse, touch, keys)."""

import importlib.util
import unittest
from unittest import mock

from pathlib import Path
import sys

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

import _env  # noqa: F401, E402

def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


HAS_JN = _has("IPython") and _has("PIL") and _has("ipywidgets") and _has("ipyevents")

if HAS_JN:
    import events
    from displaydev.jndisplay import JNDevices, JNDisplay


@unittest.skipUnless(HAS_JN, "IPython, Pillow, ipywidgets, and ipyevents required")
class TestJNDisplayDevices(unittest.TestCase):
    def setUp(self):
        with mock.patch("displaydev.jndisplay.display"), mock.patch("displaydev.jndisplay.update_display"):
            self.display = JNDisplay(320, 240, quiet=True)

    def test_ensure_devices_eager(self):
        with mock.patch("displaydev.jndisplay.display"):
            dev = self.display._ensure_devices()
            self.assertIsNotNone(dev)
            self.assertIs(self.display._jn_devices, dev)

    def test_mouse_events(self):
        with mock.patch("displaydev.jndisplay.display"):
            dev = self.display._ensure_devices()
            
            # mousedown
            dev._on_dom_event({"type": "mousedown", "button": 0, "dataX": 50, "dataY": 60})
            evs = dev.read()
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0].type, events.MOUSEBUTTONDOWN)
            self.assertEqual(evs[0].pos, (50, 60))
            self.assertEqual(evs[0].button, 1)

            # mousemove
            dev._on_dom_event({"type": "mousemove", "dataX": 55, "dataY": 65, "movementX": 5, "movementY": 5, "buttons": 1})
            evs = dev.read()
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0].type, events.MOUSEMOTION)
            self.assertEqual(evs[0].pos, (55, 65))
            self.assertEqual(evs[0].buttons, (1, 0, 0))

            # mouseup
            dev._on_dom_event({"type": "mouseup", "button": 0, "dataX": 55, "dataY": 65})
            evs = dev.read()
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0].type, events.MOUSEBUTTONUP)

    def test_touch_events(self):
        with mock.patch("displaydev.jndisplay.display"):
            dev = self.display._ensure_devices()

            # touchstart
            dev._on_dom_event({
                "type": "touchstart",
                "touches": [{"dataX": 100, "dataY": 120}],
            })
            evs = dev.read()
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0].type, events.MOUSEBUTTONDOWN)
            self.assertEqual(evs[0].pos, (100, 120))
            self.assertEqual(evs[0].button, 1)

            # touchmove
            dev._on_dom_event({
                "type": "touchmove",
                "touches": [{"dataX": 105, "dataY": 125}],
            })
            evs = dev.read()
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0].type, events.MOUSEMOTION)
            self.assertEqual(evs[0].pos, (105, 125))
            self.assertEqual(evs[0].buttons, (1, 0, 0))

            # touchend
            dev._on_dom_event({
                "type": "touchend",
                "changedTouches": [{"dataX": 105, "dataY": 125}],
            })
            evs = dev.read()
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0].type, events.MOUSEBUTTONUP)
            self.assertEqual(evs[0].pos, (105, 125))


if __name__ == "__main__":
    unittest.main()

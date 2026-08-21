# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""appdev._hostloop: who owns the main thread after the script body ends."""

import unittest

import _env  # noqa: F401

from appdev import _hostloop


class _Harness:
    """Records what hostloop asked of its owner."""

    def __init__(self, ticks=3):
        self.ticks = ticks
        self.pumped = 0
        self.started = 0
        self.stopped = 0
        self.drove = 0

    def pump(self):
        self.pumped += 1

    def alive(self):
        return self.pumped < self.ticks

    def on_start(self):
        self.started += 1

    def on_stop(self):
        self.stopped += 1

    def drive(self):
        self.drove += 1

    def install(self, **kwargs):
        kwargs.setdefault("pump", self.pump)
        kwargs.setdefault("alive", self.alive)
        kwargs.setdefault("on_start", self.on_start)
        kwargs.setdefault("on_stop", self.on_stop)
        return _hostloop.install(**kwargs)


class TestHostloop(unittest.TestCase):
    def setUp(self):
        _hostloop._reset_for_test()
        self.addCleanup(_hostloop._reset_for_test)

    def _force(self, strategy):
        _hostloop._state["strategy"] = strategy

    def test_strategy_is_none_before_install(self):
        self.assertIsNone(_hostloop.strategy())

    def test_install_decides_once_and_rebinds(self):
        first = _Harness()
        chosen = first.install()
        self.assertIn(chosen, (_hostloop.AMBIENT, _hostloop.EXIT_HOOK, _hostloop.NONE))
        second = _Harness()
        self.assertEqual(chosen, second.install())
        self.assertIs(_hostloop._state["pump"].__self__, second)

    def test_batch_entry_point_declines_to_drive(self):
        """``-m`` / ``-c`` is a test runner or a one-liner, never an app."""
        self.assertTrue(_hostloop.batch(), "the test suite itself runs under -m")
        self.assertEqual(_hostloop.NONE, _Harness().install())

    def test_exit_hook_pumps_until_not_alive(self):
        h = _Harness(ticks=4)
        h.install()
        self._force(_hostloop.EXIT_HOOK)
        _hostloop._exit_hook()
        self.assertEqual(1, h.started)
        self.assertEqual(4, h.pumped)
        self.assertEqual(1, h.stopped)

    def test_claim_suppresses_the_hook_loop(self):
        h = _Harness()
        h.install()
        self._force(_hostloop.EXIT_HOOK)
        _hostloop.claim()
        _hostloop._exit_hook()
        self.assertEqual(0, h.pumped, "run() and the hook must never both drive")
        self.assertEqual(1, h.stopped, "teardown still happens")

    def test_crashed_script_does_not_enter_the_loop(self):
        h = _Harness()
        h.install()
        self._force(_hostloop.EXIT_HOOK)
        _hostloop.mark_crashed()
        _hostloop._exit_hook()
        self.assertEqual(0, h.pumped)
        self.assertEqual(1, h.stopped)

    def test_drive_replaces_the_sync_pump_loop(self):
        """Async apps must not be driven by a loop that never runs asyncio."""
        h = _Harness()
        h.install(drive=h.drive)
        self._force(_hostloop.EXIT_HOOK)
        _hostloop._exit_hook()
        self.assertEqual(1, h.drove)
        self.assertEqual(0, h.pumped)

    def test_quit_tears_down_under_ambient_only(self):
        h = _Harness()
        h.install()
        self._force(_hostloop.EXIT_HOOK)
        _hostloop.quit()
        self.assertEqual(0, h.stopped, "the exit_hook loop notices via alive()")
        self._force(_hostloop.AMBIENT)
        _hostloop.quit()
        self.assertEqual(1, h.stopped, "nothing else would ever notice")

    def test_stop_runs_once(self):
        h = _Harness()
        h.install()
        self._force(_hostloop.AMBIENT)
        _hostloop.quit()
        _hostloop.quit()
        self.assertEqual(1, h.stopped)

    def test_split_cmdline_handles_quotes(self):
        self.assertEqual(
            ["mp.exe", "-i", "C:\\Program Files\\app.py"],
            _hostloop._split_cmdline('mp.exe -i "C:\\Program Files\\app.py"'),
        )


if __name__ == "__main__":
    unittest.main()

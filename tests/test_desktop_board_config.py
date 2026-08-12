"""Smoke / contract tests for desktop board_config (MCU-shaped, AutoDisplay)."""

import os
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
import _env  # noqa: E402, F401 — drivers/ + drivers/audio (usdl2, audiodev, …)

ROOT = _env.ROOT
DESKTOP = ROOT / "board_configs" / "desktop"

for path in (str(DESKTOP),):
    if path not in sys.path:
        sys.path.insert(0, path)


def _purge_board_modules():
    for name in list(sys.modules):
        if (
            name
            in (
                "board_config",
                "board_devices",
                "boarddev",
            )
            or name.startswith("board_config.")
            or name.startswith("board_devices.")
        ):
            sys.modules.pop(name, None)


class DesktopBoardConfigContractTests(unittest.TestCase):
    def setUp(self):
        _purge_board_modules()

    def tearDown(self):
        _purge_board_modules()

    def test_eager_mcu_shape_with_mocked_autodisplay(self):
        display = mock.Mock(name="display_drv")
        display.needs_refresh = True
        display.fill = mock.Mock()
        display.get_events = mock.Mock(name="get_events")
        display.requires_async_timer = False
        displaydev_mod = types.ModuleType("displaydev")
        displaydev_mod.env_bool = lambda name, default=False: default
        displaydev_mod.env_float = lambda name, default=0.0: default
        displaydev_mod.env_int = lambda name, default=0: default
        displaydev_auto = types.ModuleType("displaydev.auto")
        displaydev_auto.AutoDisplay = mock.Mock(return_value=display)
        displaydev_mod.auto = displaydev_auto

        with mock.patch.dict(
            sys.modules,
            {
                "displaydev": displaydev_mod,
                "displaydev.auto": displaydev_auto,
            },
        ):
            import board_config

        self.assertIs(board_config.display_drv, display)
        self.assertIs(board_config.host_read, display.get_events)
        self.assertFalse(board_config.timer_async)
        self.assertFalse(hasattr(board_config, "runtime"))
        self.assertEqual(board_config.DEVICES, frozenset({"audio_out", "audio_in"}))
        import board_devices

        self.assertTrue(callable(board_devices.audio_out))
        self.assertTrue(callable(board_devices.audio_in))
        self.assertNotIn("width", board_config.__dict__)
        self.assertNotIn("height", board_config.__dict__)
        display.fill.assert_called_once_with(0)


class DesktopBoardConfigHeadlessSmoke(unittest.TestCase):
    def setUp(self):
        _purge_board_modules()
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    def tearDown(self):
        _purge_board_modules()

    def test_import_constructs_display_and_exports_inputs(self):
        import board_config

        self.assertTrue(hasattr(board_config, "display_drv"))
        self.assertFalse(hasattr(board_config, "runtime"))
        self.assertIn("audio_out", board_config.DEVICES)
        self.assertIn("audio_in", board_config.DEVICES)
        self.assertTrue(hasattr(board_config.display_drv, "width"))
        self.assertTrue(hasattr(board_config.display_drv, "height"))
        self.assertTrue(callable(board_config.display_drv.get_events))
        self.assertFalse(hasattr(board_config, "width"))
        name = type(board_config.display_drv).__name__
        self.assertIn(name, ("PGDisplay", "SDLDisplay", "PSDisplay", "JNDisplay"))
        self.assertEqual(board_config.host_read, board_config.display_drv.get_events)

    def test_application_can_opt_into_eventsys(self):
        import board_config
        import eventsys

        runtime = eventsys.Runtime.from_board_config(board_config, refresh_period=0)
        self.addCleanup(runtime.stop_timer)
        self.assertIs(runtime.primary, board_config.display_drv)
        self.assertEqual(runtime.host_dev._read, board_config.display_drv.get_events)


if __name__ == "__main__":
    unittest.main()

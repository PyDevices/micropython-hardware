"""Smoke / contract tests for desktop board_config (MCU-shaped, AutoDisplay)."""

from pathlib import Path
import os
import sys
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "board_configs" / "desktop"
DRIVERS = ROOT / "drivers"
AUDIO = ROOT / "drivers" / "audio"
PYDISPLAY_LIB = Path.home() / "gh" / "pydevices" / "pydisplay" / "src" / "lib"

for path in (str(DESKTOP), str(DRIVERS), str(AUDIO), str(PYDISPLAY_LIB)):
    if path not in sys.path:
        sys.path.insert(0, path)


def _purge_board_modules():
    for name in list(sys.modules):
        if name in (
            "board_config",
            "board_devices",
            "boarddev",
        ) or name.startswith("board_config.") or name.startswith("board_devices."):
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
        host_read = mock.Mock(name="host_read")
        auto = types.SimpleNamespace(
            display=display,
            host_read=host_read,
            timer_async=False,
            host="desktop",
        )
        runtime = mock.Mock(name="runtime")

        # Minimal displaysys + eventsys for board_config import.
        displaysys_mod = types.ModuleType("displaysys")
        displaysys_mod.AutoDisplay = mock.Mock(return_value=auto)
        displaysys_mod.env_bool = lambda name, default=False: default
        displaysys_mod.env_float = lambda name, default=0.0: default
        displaysys_mod.env_int = lambda name, default=0: default
        displaysys_mod.env_get = lambda name, default=None: None
        displaysys_mod.env_set = lambda name, value: None

        eventsys_mod = types.ModuleType("eventsys")
        eventsys_mod.Runtime = mock.Mock(return_value=runtime)

        with mock.patch.dict(
            sys.modules,
            {"displaysys": displaysys_mod, "eventsys": eventsys_mod},
        ):
            import board_config

        self.assertIs(board_config.display_drv, display)
        self.assertIs(board_config.runtime, runtime)
        self.assertEqual(board_config.DEVICES, frozenset({"audio_out", "audio_in"}))
        # Lazy roles are bound via __getattr__; factories stay on board_devices.
        import board_devices

        self.assertTrue(callable(board_devices.audio_out))
        self.assertTrue(callable(board_devices.audio_in))
        self.assertNotIn("width", board_config.__dict__)
        self.assertNotIn("height", board_config.__dict__)
        display.fill.assert_called_once_with(0)
        eventsys_mod.Runtime.assert_called_once()
        kwargs = eventsys_mod.Runtime.call_args.kwargs
        self.assertEqual(kwargs["displays"], [display])
        self.assertIs(kwargs["host_read"], host_read)
        self.assertFalse(kwargs["timer_async"])


@unittest.skipUnless(PYDISPLAY_LIB.is_dir(), "pydisplay src/lib not found")
class DesktopBoardConfigHeadlessSmoke(unittest.TestCase):
    def setUp(self):
        _purge_board_modules()
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    def tearDown(self):
        _purge_board_modules()

    def test_import_constructs_display_and_runtime(self):
        import board_config

        self.assertTrue(hasattr(board_config, "display_drv"))
        self.assertTrue(hasattr(board_config, "runtime"))
        self.assertIsNotNone(board_config.runtime)
        self.assertIn("audio_out", board_config.DEVICES)
        self.assertIn("audio_in", board_config.DEVICES)
        self.assertTrue(hasattr(board_config.display_drv, "width"))
        self.assertTrue(hasattr(board_config.display_drv, "height"))
        # Geometry is on the driver, not board_config module attrs.
        self.assertFalse(hasattr(board_config, "width"))
        name = type(board_config.display_drv).__name__
        self.assertIn(name, ("PGDisplay", "SDLDisplay", "PSDisplay", "JNDisplay"))


if __name__ == "__main__":
    unittest.main()

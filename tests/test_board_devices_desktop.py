"""Unit tests for desktop board_devices backend selection."""

from pathlib import Path
import sys
import unittest
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
import _env  # noqa: E402, F401

sys.path.insert(0, str(_env.ROOT / "board_configs" / "desktop"))


class BoardDevicesSelectTests(unittest.TestCase):
    def setUp(self):
        for name in list(sys.modules):
            if name in ("board_devices", "boarddev") or name.startswith("board_devices"):
                sys.modules.pop(name, None)

    def _load(self):
        import board_devices

        board_devices._BACKEND = None
        return board_devices

    def test_pygame_probe_selects_pygame_audio(self):
        bd = self._load()
        with mock.patch("audiodev.auto.select_backend", return_value="pygame_audio"):
            self.assertEqual(bd._select_backend(), "pygame_audio")

    def test_desktop_without_pygame_selects_sdl2_audio(self):
        bd = self._load()
        with mock.patch("audiodev.auto.select_backend", return_value="sdl2_audio"):
            self.assertEqual(bd._select_backend(), "sdl2_audio")

    def test_pyscript_selects_web_audio(self):
        bd = self._load()
        with mock.patch("audiodev.auto.select_backend", return_value="web_audio"):
            self.assertEqual(bd._select_backend(), "web_audio")

    def test_jupyter_selects_sdl2_audio(self):
        bd = self._load()
        with mock.patch("audiodev.auto.select_backend", return_value="sdl2_audio"):
            self.assertEqual(bd._select_backend(), "sdl2_audio")

    def test_devices_roles(self):
        bd = self._load()
        self.assertEqual(bd.DEVICES, frozenset({"audio_out", "audio_in"}))


if __name__ == "__main__":
    unittest.main()

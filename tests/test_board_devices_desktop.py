"""Unit tests for desktop board_devices backend selection."""

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "board_configs" / "desktop"))
sys.path.insert(0, str(ROOT / "drivers"))
sys.path.insert(0, str(ROOT / "drivers" / "audio"))


class BoardDevicesSelectTests(unittest.TestCase):
    def setUp(self):
        for name in list(sys.modules):
            if name in ("board_devices", "boarddev") or name.startswith("board_devices"):
                sys.modules.pop(name, None)

    def _load(self):
        import board_devices

        board_devices._BACKEND = None
        return board_devices

    def test_pygame_probe_selects_pygameaudio(self):
        bd = self._load()
        with mock.patch.object(bd, "_host_kind", return_value="desktop"):
            with mock.patch.object(bd, "_pygame_available", return_value=True):
                self.assertEqual(bd._select_backend(), "pygameaudio")

    def test_desktop_without_pygame_selects_sdl2audio(self):
        bd = self._load()
        with mock.patch.object(bd, "_host_kind", return_value="desktop"):
            with mock.patch.object(bd, "_pygame_available", return_value=False):
                self.assertEqual(bd._select_backend(), "sdl2audio")

    def test_pyscript_selects_webaudio(self):
        bd = self._load()
        with mock.patch.object(bd, "_host_kind", return_value="pyscript"):
            self.assertEqual(bd._select_backend(), "webaudio")

    def test_jupyter_selects_sdl2audio(self):
        bd = self._load()
        with mock.patch.object(bd, "_host_kind", return_value="jupyter"):
            self.assertEqual(bd._select_backend(), "sdl2audio")

    def test_devices_roles(self):
        bd = self._load()
        self.assertEqual(bd.DEVICES, frozenset({"audio_out", "audio_in"}))


if __name__ == "__main__":
    unittest.main()

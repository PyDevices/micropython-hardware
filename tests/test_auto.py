"""Optional ``audiodev.auto`` selector: backends never import this module."""

import ast
from pathlib import Path
import sys
import unittest
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
import _env  # noqa: E402, F401

from audiodev import auto  # noqa: E402


class AutoSelectTests(unittest.TestCase):
    def test_pygame_xor_sdl2_on_desktop(self):
        with mock.patch.object(auto, "host_kind", return_value="desktop"):
            with mock.patch.object(auto, "_uwin32_available", return_value=False):
                with mock.patch.object(auto, "_pygame_available", return_value=True):
                    self.assertEqual(auto.select_backend(), "pygame_audio")
                with mock.patch.object(auto, "_pygame_available", return_value=False):
                    self.assertEqual(auto.select_backend(), "sdl2_audio")

    def test_win_audio_before_pygame(self):
        with mock.patch.object(auto, "host_kind", return_value="desktop"):
            with mock.patch.object(auto, "_uwin32_available", return_value=True):
                with mock.patch.object(auto, "_pygame_available", return_value=True):
                    self.assertEqual(auto.select_backend(), "win_audio")

    def test_pyscript_and_jupyter(self):
        with mock.patch.object(auto, "host_kind", return_value="pyscript"):
            self.assertEqual(auto.select_backend(), "web_audio")
        with mock.patch.object(auto, "host_kind", return_value="jupyter"):
            self.assertEqual(auto.select_backend(), "sdl2_audio")

    def test_backends_do_not_import_auto(self):
        root = _env.ROOT / "lib" / "audiodev"
        for name in (
            "sdl2_audio.py",
            "pygame_audio.py",
            "web_audio.py",
            "i2s_audio.py",
            "pwm_tone.py",
            "android_audio.py",
            "emulated_audio.py",
            "win_audio.py",
            "__init__.py",
        ):
            tree = ast.parse((root / name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module in ("audiodev.auto", ".auto"):
                        self.fail("%s imports %s" % (name, node.module))
                    if node.module == "audiodev" and any(alias.name == "auto" for alias in node.names):
                        self.fail("%s imports audiodev.auto" % name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ("audiodev.auto",):
                            self.fail("%s imports %s" % (name, alias.name))


if __name__ == "__main__":
    unittest.main()

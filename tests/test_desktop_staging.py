# SPDX-FileCopyrightText: 2026 Brad Barnett
# SPDX-License-Identifier: MIT
"""Tests for the generated ``pydevices-desktop`` source tree."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.sync_pydevices_desktop_sources import sync


class TestDesktopStaging(unittest.TestCase):
    def test_includes_cpython_micropython_shim(self):
        root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            stage = Path(tmp)
            self.assertEqual(sync(root, stage, check=False), 0)
            self.assertEqual(
                (stage / "src/micropython.py").read_bytes(),
                (root / "utils/micropython.py").read_bytes(),
            )
            self.assertIn('"micropython"', (stage / "pyproject.toml").read_text())


if __name__ == "__main__":
    unittest.main()

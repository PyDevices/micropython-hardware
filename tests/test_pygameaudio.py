"""pygame-ce backend tests (primarily CPython on Windows)."""

import asyncio
import importlib.util
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "drivers" / "audio"))

from audiodev import AudioFormat  # noqa: E402
import pygameaudio  # noqa: E402


@unittest.skipUnless(importlib.util.find_spec("pygame"), "pygame-ce is not installed")
class PygameBackendTests(unittest.TestCase):
    def test_sync_and_async_output(self):
        fmt = AudioFormat(8000, 1, 16)
        output = pygameaudio.audio_out(fmt, buffer=128)
        output.write(b"\0\0" * 80)
        output.drain()

        async def play():
            await output.awrite(b"\0\0" * 80)
            await output.adrain()

        asyncio.run(play())
        output.close()
        self.assertFalse(output.is_open)

    def test_capture_explicitly_redirects_to_reference_backend(self):
        with self.assertRaises(NotImplementedError):
            pygameaudio.audio_in()


if __name__ == "__main__":
    unittest.main()

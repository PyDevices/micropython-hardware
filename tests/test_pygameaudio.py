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

    def test_audio_in_factory_and_mocked_capture(self):
        fmt = AudioFormat(8000, 1, 16)
        capture = pygameaudio.audio_in(fmt, poll_ms=1)
        self.assertEqual(capture.format, fmt)

        stream = pygameaudio.PygameInputStream(fmt, poll_ms=1)
        stream._device = object()  # pretend open
        stream._chunks.append(b"\x01\x00\x02\x00")

        buf = bytearray(4)
        self.assertEqual(stream.readinto(buf), 4)
        self.assertEqual(bytes(buf), b"\x01\x00\x02\x00")
        stream.close()

    @unittest.skipUnless(os.getenv("PYDEVICES_TEST_REAL_AUDIO"), "real audio opt-in")
    def test_real_microphone(self):
        capture = pygameaudio.audio_in(AudioFormat(16000, 1, 16))
        buf = bytearray(1024)
        count = capture.readinto(buf)
        capture.close()
        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()

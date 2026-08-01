import asyncio
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "drivers" / "audio"))

from audiodev import AudioFormat  # noqa: E402


class SDLBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.getenv("PYDEVICES_TEST_REAL_AUDIO"):
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        global sdl2audio
        import sdl2audio

    def test_sync_output_controls_and_drain(self):
        output = sdl2audio.audio_out(AudioFormat(8000, 1, 16), queue_ms=10)
        output.set_volume(50)
        output.write((1000).to_bytes(2, "little", signed=True) * 16)
        output.mute()
        output.write(b"\xff\x7f" * 16)
        output.mute(False)
        output.drain()
        output.close()
        self.assertFalse(output.is_open)

    def test_async_output_and_cancellation(self):
        async def run():
            output = sdl2audio.audio_out(AudioFormat(8000, 1, 16), queue_ms=10)
            await output.awrite(b"\0\0" * 80)
            await output.adrain()

            async def fill_forever():
                while True:
                    await output.awrite(b"\0\0" * 80)

            task = asyncio.create_task(fill_forever())
            await asyncio.sleep(0.01)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            output.close()

        asyncio.run(run())

    @unittest.skipUnless(os.getenv("PYDEVICES_TEST_REAL_AUDIO"), "real audio opt-in")
    def test_real_microphone(self):
        capture = sdl2audio.audio_in(AudioFormat(16000, 1, 16))
        buf = bytearray(1024)
        count = capture.readinto(buf)
        capture.close()
        self.assertGreater(count, 0)
        self.assertGreater(len(set(buf[:count])), 1)


if __name__ == "__main__":
    unittest.main()

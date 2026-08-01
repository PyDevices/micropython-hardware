import asyncio
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "drivers" / "audio"))
sys.path.insert(0, str(ROOT / "examples" / "audio"))
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import usamtts  # noqa: F401
except ImportError:
    usamtts = None


@unittest.skipIf(usamtts is None, "optional usamtts dependency is not installed")
class SAMSDLTests(unittest.TestCase):
    def test_sync_end_to_end(self):
        from sam_sdl import render, speak

        pcm = render("HELLO.")
        self.assertGreater(len(pcm), 100)
        self.assertGreater(len(set(pcm[: min(len(pcm), 4096)])), 1)
        output = speak("HELLO.", chunk_size=512)
        output.close()

    def test_async_end_to_end(self):
        from sam_sdl import aspeak

        async def run():
            output = await aspeak("SAM.", chunk_size=512)
            output.close()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()

"""MicroPython Unix smoke for native usdl2 plus portable audio wrappers."""

import sys

sys.path.append("../../micropython-hardware/drivers/audio")

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

from audiodev import AudioFormat
from sdl2audio import audio_in, audio_out


async def main():
    fmt = AudioFormat(8000, 1, 16)
    output = audio_out(fmt, queue_ms=10)
    output.set_volume(50)
    await output.awrite(b"\0\0" * 80)
    await output.adrain()
    output.close()

    capture = audio_in(fmt)
    capture.open()
    await asyncio.sleep_ms(10)
    buf = bytearray(64)
    count = await capture.areadinto(buf)
    assert count > 0
    capture.close()


asyncio.run(main())
print("SDL2 audio MicroPython smoke: PASS")

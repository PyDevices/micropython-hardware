"""End-to-end SAM text-to-speech playback through the SDL audio backend.

SAM is an optional external dependency. The compatible ``usamtts`` module is
not vendored because its upstream project has no open-source license.
"""

from audiodev import AudioFormat
from sdl2audio import audio_out
from usamtts import Processor, Reciter, Renderer

SAM_FORMAT = AudioFormat(22050, 1, 8, signed=False)


def render(text, *, reciter=None, processor=None, renderer=None):
    """Synthesize text and return SAM's unsigned 8-bit mono PCM view."""
    reciter = reciter or Reciter()
    processor = processor or Processor()
    renderer = renderer or Renderer()
    processor.process(reciter.text_to_phonemes(text))
    renderer.render(processor)
    return memoryview(renderer.buffer)[: renderer.buffer_end]


def speak(text, output=None, *, chunk_size=2048):
    """Synchronously synthesize and play text."""
    output = output or audio_out(SAM_FORMAT)
    pcm = render(text)
    for offset in range(0, len(pcm), chunk_size):
        output.write(pcm[offset : offset + chunk_size])
    output.drain()
    return output


async def aspeak(text, output=None, *, chunk_size=2048):
    """Synthesize, then cooperatively queue and play text."""
    output = output or audio_out(SAM_FORMAT)
    pcm = render(text)
    for offset in range(0, len(pcm), chunk_size):
        await output.awrite(pcm[offset : offset + chunk_size])
    await output.adrain()
    return output


if __name__ == "__main__":
    device = speak("Hello. My name is Sam.")
    device.close()

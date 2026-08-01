"""Stream Gemini 3.1 TTS to the default SDL audio output.

Set ``GEMINI_API_KEY`` before running. On CPython, optional command-line words
replace the demonstration passage::

    python gemini_sdl.py "Hello from streaming Gemini speech."
"""

import os
import sys
import time

from audiodev import AudioFormat
from sdl2audio import audio_out
from tts import GeminiTTS, TTSClient


DEFAULT_TEXT = (
    "This is Gemini text to speech streaming through the portable audio device. "
    "Playback begins when the first audio samples arrive, while Gemini continues "
    "generating the rest of this passage. SDL maintains a short queue so the "
    "speaker remains smooth without waiting for the complete recording."
)


def _milliseconds():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.monotonic() * 1000)


def _elapsed(start, end):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(end, start)
    return end - start


def main(text=DEFAULT_TEXT):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("set GEMINI_API_KEY before running this example")

    output = audio_out(AudioFormat(24000, 1, 16), queue_ms=150)
    client = TTSClient(GeminiTTS(key), chunk_size=4096)
    started = _milliseconds()
    stream = client.stream(
        text,
        instructions="Read clearly in a friendly, relaxed voice.",
    )
    first_audio = None
    chunks = 0
    total = 0
    try:
        for pcm in stream:
            if first_audio is None:
                first_audio = _milliseconds()
            chunks += 1
            total += output.write(pcm)
        stream_complete = _milliseconds()
        output.drain()
        playback_complete = _milliseconds()
    finally:
        stream.close()
        output.close()

    if first_audio is None:
        raise RuntimeError("Gemini returned no audio")
    print("audio chunks:", chunks)
    print("PCM bytes:", total)
    print("first audio: %d ms" % _elapsed(started, first_audio))
    print("stream complete: %d ms" % _elapsed(started, stream_complete))
    print("playback complete: %d ms" % _elapsed(started, playback_complete))
    print(
        "generation/playback overlap: %d ms"
        % _elapsed(first_audio, stream_complete)
    )


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TEXT)

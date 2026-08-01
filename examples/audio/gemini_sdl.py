"""Stream Gemini 3.1 TTS to the default SDL audio output.

Copy ``secrets.py.example`` to ``secrets.py`` beside this file and put your
Gemini API key in it before running::

    GEMINI_API_KEY = "your-key"
"""

from audiodev import AudioFormat
from multimer import ticks_diff, ticks_ms
from sdl2audio import audio_out
from secrets import GEMINI_API_KEY
from tts import GeminiTTS, TTSClient


DEFAULT_TEXT = (
    "This is Gemini text to speech streaming through the portable audio device. "
    "Playback begins when the first audio samples arrive, while Gemini continues "
    "generating the rest of this passage. SDL maintains a short queue so the "
    "speaker remains smooth without waiting for the complete recording."
)


def main(text=DEFAULT_TEXT):
    output = audio_out(AudioFormat(24000, 1, 16), queue_ms=150)
    client = TTSClient(GeminiTTS(GEMINI_API_KEY), chunk_size=4096)
    started = ticks_ms()
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
                first_audio = ticks_ms()
            chunks += 1
            total += output.write(pcm)
        stream_complete = ticks_ms()
        output.drain()
        playback_complete = ticks_ms()
    finally:
        stream.close()
        output.close()

    if first_audio is None:
        raise RuntimeError("Gemini returned no audio")
    print("audio chunks:", chunks)
    print("PCM bytes:", total)
    print("first audio: %d ms" % ticks_diff(first_audio, started))
    print("stream complete: %d ms" % ticks_diff(stream_complete, started))
    print("playback complete: %d ms" % ticks_diff(playback_complete, started))
    print(
        "generation/playback overlap: %d ms"
        % ticks_diff(stream_complete, first_audio)
    )


if __name__ == "__main__":
    main()

# Portable audio

The audio surface is split by direction: boards expose `audio_out` and/or
`audio_in`. Each object owns stream lifecycle and reports an `AudioFormat` plus
a `capabilities` set. PCM output supports `write`, `drain`, `awrite`, and
`adrain`; PCM input supports `readinto` and `areadinto`. Volume, gain, and mute
use a normalized 0–100 scale and select hardware controls when a codec provides
them, otherwise `audiodev` scales PCM in software.

Codec-specific features remain reachable through `device.codec`. Shared
half-duplex hardware uses `AudioSession`; opening the opposite direction while
one direction owns the session raises `OSError`.

## Host backends

`sdl2audio.py` is the reference playback and real-microphone backend for
MicroPython and CPython. It uses queued SDL audio and provides the same sync and
async contract as hardware devices. `pygameaudio.py` provides CPython playback,
primarily for pygame-ce applications on Windows. pygame-ce has no public capture
API, so applications use `sdl2audio.audio_in` for host microphones.

## Speech

The SAM example synthesizes locally and writes its PCM directly to an
`audio_out` device. `tts.py` supplies optional streaming HTTP adapters for
OpenAI, ElevenLabs, Azure, Google Cloud, and Gemini and sends provider-neutral
PCM chunks through the same device contract. Wit.ai is an audio-input speech
recognition/NLU service rather than a text-to-speech provider, so it belongs on
the capture/upload side and is not presented as a TTS backend.

## ESP32-P4 status

The Waveshare ESP32-P4 configuration uses one half-duplex session for its I2S
peripheral and ES8311. Playback exposes hardware DAC volume/mute and controls
the speaker amplifier; capture exposes hardware ADC gain. Register, stream,
session, and GPIO behavior is covered by host simulations. Physical electrical
and acoustic validation is pending access to the board.

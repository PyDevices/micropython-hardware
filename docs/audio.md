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
async contract as hardware devices.

`pygameaudio.py` provides CPython playback and capture for pygame-ce hosts
(typically Windows / `python.exe`). Playback uses `pygame.mixer`; capture uses
`pygame._sdl2.AudioDevice` (`iscapture=True`).

`webaudio.py` provides PyScript / browser playback (`AudioContext`) and capture
(`getUserMedia`).

Desktop `board_devices` selects a backend by host probe (`import pygame`,
`import pyscript`, or Jupyter / SDL fallback) without importing `displaysys`.

## WAV file devices (MCU-safe)

`audiodev.wav_output(path, format)` and `audiodev.wav_input(path)` implement
file-backed `PCMOutput` / `PCMInput` for PCM WAV only. Use them to record a
prompt to storage or to simulate a microphone on boards that already ship
`audiodev` without the desktop audio package:

```python
from audiodev import AudioFormat, wav_input, wav_output

fmt = AudioFormat(24000, 1, 16)
out = wav_output("/sd/prompt.wav", fmt)
out.write(pcm_bytes)
out.close()

mic = wav_input("/sd/prompt.wav")
```


## ESP32-P4 status

The Waveshare ESP32-P4 configuration uses one half-duplex session for its I2S
peripheral and ES8311. Playback exposes hardware DAC volume/mute and controls
the speaker amplifier; capture exposes hardware ADC gain. Register, stream,
session, and GPIO behavior is covered by host simulations.

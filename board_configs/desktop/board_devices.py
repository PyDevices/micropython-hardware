"""Lazy constructors for desktop non-UI devices. DEVICES = lazy roles only."""

import sys

import boarddev

DEVICES = frozenset({"audio_out", "audio_in"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def audio_out():
    from audiodev import AudioFormat
    from sdl2audio import audio_out as _sdl_audio_out

    return _sdl_audio_out(AudioFormat(24000, 1, 16), queue_ms=150)


def audio_in():
    from audiodev import AudioFormat
    from sdl2audio import audio_in as _sdl_audio_in

    return _sdl_audio_in(AudioFormat(24000, 1, 16), queue_ms=150)

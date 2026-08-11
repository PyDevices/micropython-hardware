"""Lazy audio devices for the dedicated JNDisplay board package."""

import sys

import boarddev

DEVICES = frozenset({"audio_out", "audio_in"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def _format():
    from audiodev import AudioFormat

    return AudioFormat(24000, 1, 16)


def audio_out(**kwargs):
    """Build the playback device; keywords go straight to the backend.

    A notebook cell drives the pump from its own loop, so the queue is kept
    short by default rather than at the backend's buffered depth.
    """
    from audiodev.sdl2_audio import audio_out as _audio_out

    kwargs.setdefault("queue_ms", 150)
    return _audio_out(_format(), **kwargs)


def audio_in(**kwargs):
    """Build the capture device; see :func:`audio_out` for the keyword contract."""
    from audiodev.sdl2_audio import audio_in as _audio_in

    kwargs.setdefault("queue_ms", 150)
    return _audio_in(_format(), **kwargs)

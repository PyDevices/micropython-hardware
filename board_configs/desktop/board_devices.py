"""Lazy constructors for desktop non-UI devices. DEVICES = lazy roles only."""

import sys

import boarddev

_FORMAT = None
_BACKEND = None

DEVICES = frozenset({"audio_out", "audio_in"})


def _host_kind():
    try:
        import pyscript  # noqa: F401

        return "pyscript"
    except Exception:
        pass
    try:
        get_ipython()  # noqa: F821
        return "jupyter"
    except Exception:
        return "desktop"


def _pygame_available():
    try:
        import pygame  # noqa: F401

        return True
    except Exception:
        return False


def _select_backend():
    global _BACKEND
    if _BACKEND is not None:
        return _BACKEND
    host = _host_kind()
    if host == "pyscript":
        _BACKEND = "webaudio"
    elif host == "jupyter":
        _BACKEND = "sdl2audio"
    elif _pygame_available():
        _BACKEND = "pygameaudio"
    else:
        _BACKEND = "sdl2audio"
    return _BACKEND


def _audio_format():
    global _FORMAT
    if _FORMAT is None:
        from audiodev import AudioFormat

        _FORMAT = AudioFormat(24000, 1, 16)
    return _FORMAT


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def audio_out():
    fmt = _audio_format()
    backend = _select_backend()
    if backend == "webaudio":
        from webaudio import audio_out as _audio_out
    elif backend == "pygameaudio":
        from pygameaudio import audio_out as _audio_out
    else:
        from sdl2audio import audio_out as _audio_out

    return _audio_out(fmt, queue_ms=150) if backend == "sdl2audio" else _audio_out(fmt)


def audio_in():
    fmt = _audio_format()
    backend = _select_backend()
    if backend == "webaudio":
        from webaudio import audio_in as _audio_in
    elif backend == "pygameaudio":
        from pygameaudio import audio_in as _audio_in
    else:
        from sdl2audio import audio_in as _audio_in

    return _audio_in(fmt, queue_ms=150) if backend == "sdl2audio" else _audio_in(fmt)

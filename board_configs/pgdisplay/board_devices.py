"""Lazy audio devices for the dedicated PGDisplay board package."""

import sys

import boarddev

DEVICES = frozenset({"audio_out", "audio_in"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def _format():
    from audiodev import AudioFormat

    return AudioFormat(24000, 1, 16)


def audio_out():
    from pygameaudio import audio_out as _audio_out

    return _audio_out(_format())


def audio_in():
    from pygameaudio import audio_in as _audio_in

    return _audio_in(_format())

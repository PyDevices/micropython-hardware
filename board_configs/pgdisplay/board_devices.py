"""Lazy audio devices for the dedicated PGDisplay board package."""

import sys

import boarddev

if sys.platform == "win32":
    from displaysys import env_get, env_set

    # See board_config.py for the full rationale (SDL2's default Windows
    # WASAPI backend glitches with pygame.mixer.Channel's small-chunk
    # playback; DirectSound does not). Duplicated here because an app can
    # init board_devices directly without ever importing board_config (e.g.
    # examples/audio_out_test.py), and audio_out()/audio_in() below open the
    # pygame mixer lazily on first use -- this must land before that, and
    # before any board_config PGDisplay pg.init(), whichever runs first.
    # Only when unset, so an explicit user choice still wins.
    if env_get("SDL_AUDIODRIVER") is None:
        env_set("SDL_AUDIODRIVER", "directsound")

DEVICES = frozenset({"audio_out", "audio_in"})


def setup_devices(ns):
    boarddev.bind_lazy(ns, sys.modules[__name__])


def _format():
    from audiodev import AudioFormat

    return AudioFormat(24000, 1, 16)


def audio_out(**kwargs):
    """Build the playback device; keywords go straight to the backend."""
    from audiodev.pygame_audio import audio_out as _audio_out

    return _audio_out(_format(), **kwargs)


def audio_in(**kwargs):
    """Build the capture device; keywords go straight to the backend."""
    from audiodev.pygame_audio import audio_in as _audio_in

    return _audio_in(_format(), **kwargs)

"""Universal non-MCU board configuration (desktop / Jupyter / PyScript)."""

import sys

import eventsys
from displaysys import AutoDisplay, env_bool, env_float, env_get, env_int, env_set

if sys.platform == "win32":
    # SDL2's default Windows audio driver (WASAPI) has a compatibility issue
    # with pygame.mixer.Channel's play()/queue() small-chunk playback pattern
    # that produces periodic audible glitches (confirmed via runtime A/B test:
    # SDL_AUDIODRIVER=directsound is glitch-free with identical PCM output).
    # Must be set before AutoDisplay → PGDisplay's pg.init() -- SDL locks in
    # its audio driver at the first SDL_InitSubSystem(SDL_INIT_AUDIO) call, and
    # pygameaudio.py opens the mixer lazily on first audio_out() use, well
    # after that has already happened. An explicit user choice is left alone.
    # env_set, not os.environ: MicroPython Windows is ``win32`` too and has
    # only os.putenv, so os.environ would raise here on import.
    if env_get("SDL_AUDIODRIVER") is None:
        env_set("SDL_AUDIODRIVER", "directsound")

_width = env_int("PYDISPLAY_WIDTH", 320)
_height = env_int("PYDISPLAY_HEIGHT", 480)
_rotation = env_int("PYDISPLAY_ROTATION", 0)
_scale = env_float("PYDISPLAY_SCALE", 2.0)

_auto = AutoDisplay(
    width=_width,
    height=_height,
    rotation=_rotation,
    scale=_scale,
    title="{} on {}".format(sys.implementation.name, sys.platform),
)

display_drv = _auto.display
runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=_auto.host_read,
    timer_async=env_bool("PYDISPLAY_TIMER_ASYNC", _auto.timer_async),
)

display_drv.fill(0)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

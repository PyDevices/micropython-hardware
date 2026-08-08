"""
Board configuration for PyGame.
"""

import sys

if sys.platform == "win32":
    import os

    # SDL2's default Windows audio driver (WASAPI) has a compatibility issue
    # with pygame.mixer.Channel's play()/queue() small-chunk playback pattern
    # that produces periodic audible glitches (confirmed: identical PCM output
    # via SDL_AUDIODRIVER=directsound is glitch-free; SDL_QueueAudio-based
    # output, e.g. drivers/audio/sdl2audio.py, is unaffected on Windows either
    # way). DirectSound is SDL2's own supported alternative Windows backend.
    # Must be set here, before PGDisplay's pg.init() below -- SDL locks in its
    # audio driver at the first SDL_InitSubSystem(SDL_INIT_AUDIO), so setting
    # this later in drivers/audio/pygameaudio.py (which opens the mixer lazily
    # on first audio_out() use, well after PGDisplay has already called
    # pg.init()) is too late. setdefault() leaves an explicit user choice alone.
    os.environ.setdefault("SDL_AUDIODRIVER", "directsound")

from displaysys.pgdisplay import PGDisplay as DTDisplay
import eventsys

width = 320
height = 480
rotation = 0
scale = 2.0

display_drv = DTDisplay(
    width=width,
    height=height,
    rotation=rotation,
    title=f"{sys.implementation.name} on {sys.platform}",
    scale=scale,
)

runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=display_drv.get_events,
)

display_drv.fill(0)

from board_devices import DEVICES, setup_devices

setup_devices(globals())

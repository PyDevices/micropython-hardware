"""Universal non-MCU board configuration.

This module targets desktop-like hosts (CPython, MicroPython unix/windows,
Jupyter, and PyScript). Runtime/display initialization is lazy so importing
``board_config`` does not require active SDL/audio devices.
"""

import sys

from displaysys import env_bool, env_float, env_get, env_int, env_set

if sys.platform == "win32":
    # SDL2's default Windows audio driver (WASAPI) has a compatibility issue
    # with pygame.mixer.Channel's play()/queue() small-chunk playback pattern
    # that produces periodic audible glitches (confirmed via runtime A/B test:
    # SDL_AUDIODRIVER=directsound is glitch-free with identical PCM output).
    # Must be set before PGDisplay's pg.init() in _desktop_display() below --
    # SDL locks in its audio driver at the first SDL_InitSubSystem(SDL_INIT_AUDIO)
    # call, and pygameaudio.py opens the mixer lazily on first audio_out() use,
    # well after that has already happened. An explicit user choice is left
    # alone. env_set, not os.environ: MicroPython Windows is ``win32`` too and
    # has only os.putenv, so os.environ would raise here on import.
    if env_get("SDL_AUDIODRIVER") is None:
        env_set("SDL_AUDIODRIVER", "directsound")

DEFAULT_TIMER_ASYNC = False

width = 320
height = 480
rotation = 0
scale = 2.0

width = env_int("PYDISPLAY_WIDTH", width)
height = env_int("PYDISPLAY_HEIGHT", height)
scale = env_float("PYDISPLAY_SCALE", scale)


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


def _make_runtime(display, host_read, timer_async):
    import eventsys

    return eventsys.Runtime(
        displays=[display],
        host_read=host_read,
        timer_async=timer_async,
    )


def _desktop_display(title):
    try:
        from displaysys.pgdisplay import PGDisplay as DTDisplay
        from displaysys.pgdisplay import get_events
    except Exception:
        from displaysys.sdldisplay import SDLDisplay as DTDisplay
        from displaysys.sdldisplay import get_events

    display = DTDisplay(
        width=width,
        height=height,
        rotation=rotation,
        title=title,
        scale=scale,
    )
    return display, get_events


_INITIALIZED = False
DEVICES = frozenset()


def _init_runtime():
    global _INITIALIZED
    global DEVICES

    if _INITIALIZED:
        return

    host = _host_kind()

    if host == "pyscript":
        from displaysys.psdisplay import PSDevices, PSDisplay

        display_drv = PSDisplay("display_canvas", width, height)
        devices_drv = PSDevices("display_canvas", display_drv)
        runtime = _make_runtime(display_drv, devices_drv.read, timer_async=True)
    elif host == "jupyter":
        from displaysys.jndisplay import JNDevices, JNDisplay

        display_drv = JNDisplay(width, height)
        devices_drv = JNDevices(display_drv)
        runtime = _make_runtime(display_drv, devices_drv.read, timer_async=True)
    else:
        display_drv, get_events = _desktop_display(
            "{} on {}".format(sys.implementation.name, sys.platform)
        )
        runtime = _make_runtime(
            display_drv,
            get_events,
            timer_async=env_bool("PYDISPLAY_TIMER_ASYNC", DEFAULT_TIMER_ASYNC),
        )

    from board_devices import DEVICES as _DEVICES, setup_devices

    DEVICES = _DEVICES
    setup_devices(globals())

    globals()["display_drv"] = display_drv
    globals()["runtime"] = runtime
    display_drv.fill(0)
    _INITIALIZED = True


def __getattr__(name):
    if name in ("display_drv", "runtime", "audio_out", "audio_in"):
        _init_runtime()
        if name in globals():
            return globals()[name]
        current_getattr = globals().get("__getattr__")
        if current_getattr is not None and current_getattr is not _BOOTSTRAP_GETATTR:
            return current_getattr(name)
    raise AttributeError("module has no attribute {!r}".format(name))


_BOOTSTRAP_GETATTR = __getattr__


def __dir__():
    names = set(globals().keys())
    names.update(("display_drv", "runtime"))
    names.update(DEVICES)
    return sorted(names)

"""Universal non-MCU board configuration.

This module targets desktop-like hosts (CPython, MicroPython unix/windows,
Jupyter, and PyScript). Runtime/display initialization is lazy so importing
``board_config`` does not require active SDL/audio devices.
"""

import os
import sys

DEFAULT_TIMER_ASYNC = False

width = 320
height = 480
rotation = 0
scale = 2.0


def _env_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    return default


def _env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


def _env_float(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


width = _env_int("PYDISPLAY_WIDTH", width)
height = _env_int("PYDISPLAY_HEIGHT", height)
scale = _env_float("PYDISPLAY_SCALE", scale)


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
_MISSING = object()


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
            timer_async=_env_bool("PYDISPLAY_TIMER_ASYNC", DEFAULT_TIMER_ASYNC),
        )

        class _DesktopDevices:
            DEVICES = frozenset(("audio_out", "audio_in"))

            @staticmethod
            def audio_out():
                from audiodev import AudioFormat
                from sdl2audio import audio_out as _sdl_audio_out

                return _sdl_audio_out(AudioFormat(24000, 1, 16), queue_ms=150)

            @staticmethod
            def audio_in():
                from audiodev import AudioFormat
                from sdl2audio import audio_in as _sdl_audio_in

                return _sdl_audio_in(AudioFormat(24000, 1, 16), queue_ms=150)

        DEVICES = _DesktopDevices.DEVICES

        import boarddev

        boarddev.bind_lazy(globals(), _DesktopDevices)

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
    names.update(("display_drv", "runtime", "audio_out", "audio_in"))
    return sorted(names)

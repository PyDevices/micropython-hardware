# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Run the portable audio path under MicroPython or CircuitPython.

``test_portability.py`` runs this under every non-CPython interpreter it can
find. It is also useful by hand::

    cd micropython-hardware
    micropython tests/portability_probe.py
    micropython.exe tests/portability_probe.py
    circuitpython tests/portability_probe.py

It exercises the two things that have actually broken -- selecting a backend
(which sets ``SDL_AUDIODRIVER`` on Windows) and writing PCM (which consumes
bytearray buffers). Neither fails at import, only on first use, so importing the
modules is not enough to prove anything.

This file must itself stay inside the API subset MicroPython and CircuitPython
share: no ``os.path``, no ``pathlib``, no ``unittest``, no ``os.environ``.
Prints ``PORTABILITY OK`` on success; raises (exit 1) on the first failure.
"""

import os
import sys

_SLASH = __file__.replace("\\", "/")
ROOT = _SLASH.rsplit("/", 1)[0] + "/.." if "/" in _SLASH else ".."

for _rel in ("drivers", "drivers/audio", "board_configs/desktop"):
    sys.path.insert(0, ROOT + "/" + _rel)

# Headless, and set before SDL initializes either subsystem. Done here rather
# than by the caller because WSL does not forward its environment into
# micropython.exe.
os.putenv("SDL_VIDEODRIVER", "dummy")

_checks = 0


def check(label, ok):
    global _checks
    if not ok:
        raise AssertionError(label)
    _checks += 1
    print("  ok:", label)


def probe_backend_selection():
    """``_select_backend()`` used to reach ``os.environ`` and die on win32."""
    preset = os.getenv("SDL_AUDIODRIVER")

    import board_devices

    backend = board_devices._select_backend()
    check(
        "selected a backend ({})".format(backend),
        backend in ("sdl2audio", "pygameaudio", "webaudio"),
    )
    current = os.getenv("SDL_AUDIODRIVER")
    if sys.platform == "win32":
        check("win32 sets an audio driver", current is not None)
        if preset is None:
            check("win32 defaults to directsound", current == "directsound")
        else:
            check("an explicit audio driver still wins", current == preset)
    else:
        check("non-win32 leaves the audio driver alone", current == preset)


def probe_buffer_consumption():
    """Writing PCM used to raise ``TypeError`` on bytearray item deletion."""
    # Never open the real sink from a test: a second stream on the host sink
    # fights whatever else is playing, and this way no audio hardware is needed.
    os.putenv("SDL_AUDIODRIVER", "dummy")

    from audiodev import AudioFormat
    import sdl2audio

    fmt = AudioFormat(24000, 1, 16)
    device = sdl2audio.audio_out(fmt)
    device.open()
    stream = device.stream

    # Small enough that the first queued piece overflows it, so the trim branch
    # runs without writing megabytes.
    stream._shadow_limit = 1024

    # A recognizable ramp, so the checks below can tell the tail of the buffer
    # from the head -- a slice that trimmed the wrong end would still have the
    # right length.
    pattern = bytearray()
    for value in range(256):
        pattern.append(value)

    piece = stream._coalesce_bytes
    written = bytearray()
    while len(written) < piece + piece // 2:
        written.extend(pattern)

    stream.write(written)
    stream.service()

    check("queued PCM to SDL ({} bytes)".format(stream._queued_total), stream._queued_total > 0)
    check(
        "consumed from the front of _coalesce ({} left)".format(len(stream._coalesce)),
        len(stream._coalesce) == len(written) - stream._queued_total,
    )
    check(
        "trimmed _shadow to its limit ({} bytes)".format(len(stream._shadow)),
        len(stream._shadow) <= stream._shadow_limit,
    )
    check(
        "_shadow kept the tail, not the head",
        bytes(stream._shadow)
        == bytes(written[: stream._queued_total])[-stream._shadow_limit :],
    )

    stream.clear()
    check(
        "clear() empties both buffers",
        len(stream._coalesce) == 0 and len(stream._shadow) == 0,
    )
    device.close()


def probe_board_config():
    """``board_config`` is what apps import; it must load headless."""
    try:
        import displaysys  # noqa: F401
    except ImportError:
        print("  skip: displaysys is not installed for this interpreter")
        return

    import board_config

    check("board_config built a display", hasattr(board_config, "display_drv"))
    check("board_config built a runtime", hasattr(board_config, "runtime"))
    check("board_config bound the audio roles", "audio_out" in board_config.DEVICES)


def main():
    probe_backend_selection()
    probe_buffer_consumption()
    probe_board_config()
    print(
        "PORTABILITY OK ({} checks, {} {})".format(
            _checks, sys.implementation.name, sys.platform
        )
    )


try:
    main()
except Exception as exc:
    # Re-raised so the interpreter prints a traceback and exits non-zero.
    print("FAIL:", exc)
    raise

# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""Benchmark ``displaydev.windisplay`` throughput and allocation.

Windows only. Runs from WSL against ``python.exe`` / ``micropython.exe``::

    python.exe tools/bench_windisplay.py
    micropython.exe -X heapsize=64M tools/bench_windisplay.py

Reports frames/s for a full-frame repaint, a small-rect repaint, and a
scrolled repaint, plus bytes allocated per frame where the interpreter can
measure it.
"""

import gc
import sys
import time

for _p in ("lib", "utils"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

WIDTH = 320
HEIGHT = 240
FRAMES = 120


def _mem():
    """Bytes currently allocated, or None when the port cannot say."""
    try:
        return gc.mem_alloc()  # MicroPython
    except AttributeError:
        pass
    try:
        import tracemalloc

        if tracemalloc.is_tracing():
            return tracemalloc.get_traced_memory()[0]
    except ImportError:
        pass
    return None


def _ticks_us():
    try:
        return time.ticks_us()  # MicroPython
    except AttributeError:
        return int(time.monotonic() * 1_000_000)


def _elapsed_us(start):
    try:
        return time.ticks_diff(_ticks_us(), start)
    except AttributeError:
        return _ticks_us() - start


def _pattern(width, height):
    """A gradient + block test pattern as RGB565 little-endian bytes."""
    buf = bytearray(width * height * 2)
    for y in range(height):
        base = y * width * 2
        g = (y * 63) // max(1, height - 1)
        for x in range(width):
            r = (x * 31) // max(1, width - 1)
            b = 31 - r
            c = (r << 11) | (g << 5) | b
            o = base + x * 2
            buf[o] = c & 0xFF
            buf[o + 1] = c >> 8
    return buf


def _bench(name, fn, frames=FRAMES):
    gc.collect()
    before = _mem()
    start = _ticks_us()
    for i in range(frames):
        fn(i)
    us = _elapsed_us(start)
    after = _mem()
    fps = frames * 1_000_000.0 / us if us else float("inf")
    per_frame = ""
    if before is not None and after is not None:
        per_frame = "  {:>9.0f} B/frame".format(max(0, after - before) / frames)
    print("  {:<22} {:>8.1f} fps   {:>8.2f} ms/frame{}".format(name, fps, us / 1000.0 / frames, per_frame))
    return fps


def main():
    if sys.platform != "win32":
        print("bench_windisplay: Windows only (got {})".format(sys.platform))
        return 1

    try:
        import tracemalloc

        tracemalloc.start()
    except ImportError:
        pass

    from displaydev.windisplay import WinDisplay, get_events

    impl = getattr(sys.implementation, "name", "?")
    print("bench_windisplay: {} on {}  {}x{}  {} frames".format(impl, sys.platform, WIDTH, HEIGHT, FRAMES))

    scale = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    display = WinDisplay(width=WIDTH, height=HEIGHT, scale=scale, title="bench", quiet=True)
    pattern = _pattern(WIDTH, HEIGHT)
    small = _pattern(32, 32)

    resident = 0
    for attr in ("_buffer", "_visible", "_bgra"):
        buf = getattr(display, attr, None)
        if buf is not None:
            resident += len(buf)
            print("  resident {:<12} {:>9} B".format(attr, len(buf)))
    print("  resident {:<12} {:>9} B  ({:.1f} B/px)".format("TOTAL", resident, resident / float(WIDTH * HEIGHT)))
    print("  scale {} -> {:.4f}, banded partial presents: {}".format(
        scale, display._scale, getattr(display, "_can_band", False)))
    print("")

    def full(i):
        display.blit_rect(pattern, 0, 0, WIDTH, HEIGHT)
        display.show()
        get_events()

    def small_rect(i):
        display.blit_rect(small, (i * 7) % (WIDTH - 32), (i * 5) % (HEIGHT - 32), 32, 32)
        display.show()
        get_events()

    def idle(i):
        display.show()
        get_events()

    display.blit_rect(pattern, 0, 0, WIDTH, HEIGHT)
    display.show()

    _bench("full-frame blit", full)
    _bench("32x32 blit", small_rect)
    _bench("idle (no draws)", idle)

    display.vscrdef(0, HEIGHT, 0)

    def scrolled(i):
        display.vscsad(i % HEIGHT)
        display.show()
        get_events()

    _bench("scrolled", scrolled)
    display.vscsad(False)

    display.deinit()
    return 0


if __name__ == "__main__":
    sys.exit(main())

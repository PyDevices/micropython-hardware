# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Prove displaydev and multimer are standalone with respect to each other.

Each test copies *only* one package into a temporary directory and imports it
in a fresh subprocess whose path contains nothing else from the repository.
``displaydev`` also receives shared ``events.py`` / ``keys.py``.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

import _env

_MULTIMER_SIBLINGS = ("displaydev", "eventsys", "pygraphics", "palettes", "audiodev")
_DISPLAYDEV_SIBLINGS = ("eventsys", "pygraphics", "multimer", "palettes", "audiodev")

_MULTIMER_CHILD = textwrap.dedent(
    """
    import sys

    import time

    import multimer
    from multimer import (
        AsyncTimer,
        schedule,
        ticks_add,
        ticks_diff,
        ticks_less,
        ticks_ms,
    )
    from multimer import auto as timer

    forbidden = [m for m in {siblings!r} if m in sys.modules]
    assert not forbidden, "multimer pulled in sibling modules: %r" % forbidden

    assert ticks_ms() >= 0
    seen = []
    schedule(lambda x: seen.append(x), 1)
    assert seen == [1], seen

    hits = []
    t = timer.Timer(-1)
    t.init(period=50, callback=lambda tim: hits.append(tim))
    deadline = time.monotonic() + 0.35
    while time.monotonic() < deadline:
        timer.sleep_ms(10)
    t.deinit()
    assert hits, "standalone timer never fired"
    assert AsyncTimer is not None, "AsyncTimer should be available on CPython"

    print("STANDALONE_OK")
    """
).format(siblings=list(_MULTIMER_SIBLINGS))


_DISPLAYDEV_CHILD = textwrap.dedent(
    """
    import sys

    import displaydev
    import events
    import keys
    from displaydev import (
        alloc_buffer,
        color332,
        color565,
        color565_swapped,
        color_rgb,
    )
    from displaydev._domkeys import key_to_keycode
    from displaydev.fbdisplay import FBDisplay


    class FakeFrameBuffer:
        def __init__(self, width, height, bpp=2):
            self.width = width
            self.height = height
            self.data = bytearray(width * height * bpp)

        def __buffer__(self, flags):
            return memoryview(self.data)

        def refresh(self):
            pass


    forbidden = [m for m in {siblings!r} if m in sys.modules]
    assert not forbidden, "displaydev pulled in sibling modules: %r" % forbidden

    assert color565(255, 255, 255) == 0xFFFF
    assert color_rgb(0x0000) == (0, 0, 0)
    assert len(alloc_buffer(8)) == 8

    fb = FakeFrameBuffer(4, 2)
    d = FBDisplay(fb)
    d.fill(0xFFFF)
    assert bytes(fb.data) == b"\\xff\\xff" * 8, "FBDisplay.fill did not paint buffer"
    d.deinit()

    assert "multimer" not in sys.modules, "displaydev imported multimer unexpectedly"
    assert "eventsys" not in sys.modules, "displaydev imported eventsys"
    assert events.QUIT == 0x100
    assert keys.K_q
    assert key_to_keycode("BrowserBack", 0) == keys.K_AC_BACK

    print("STANDALONE_OK")
    """
).format(siblings=list(_DISPLAYDEV_SIBLINGS))


class TestStandalone(unittest.TestCase):
    def test_multimer_imports_and_runs_in_isolation(self):
        tmp = tempfile.mkdtemp(prefix="multimer_standalone_")
        try:
            shutil.copytree(_env.MULTIMER_DIR, os.path.join(tmp, "multimer"))

            env = dict(os.environ)
            env["PYTHONPATH"] = tmp

            proc = subprocess.run(
                [sys.executable, "-c", _MULTIMER_CHILD],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                proc.returncode,
                0,
                msg=f"child failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            )
            self.assertIn("STANDALONE_OK", proc.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_displaydev_imports_and_runs_in_isolation(self):
        tmp = tempfile.mkdtemp(prefix="displaydev_standalone_")
        try:
            shutil.copytree(_env.DISPLAYDEV_DIR, os.path.join(tmp, "displaydev"))
            shutil.copyfile(_env.EVENTS_PY, os.path.join(tmp, "events.py"))
            shutil.copyfile(_env.KEYS_PY, os.path.join(tmp, "keys.py"))

            env = dict(os.environ)
            env["PYTHONPATH"] = tmp

            proc = subprocess.run(
                [sys.executable, "-c", _DISPLAYDEV_CHILD],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                proc.returncode,
                0,
                msg=f"child failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            )
            self.assertIn("STANDALONE_OK", proc.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

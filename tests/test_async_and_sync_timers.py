# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Dedicated test suite validating async and synchronous timer backends in appdev."""

import time
import unittest

import _env  # noqa: F401

import events
import keys
import appdev
from appdev import App
from multimer import AsyncTimer, auto as timer


class _FakeDisplay:
    def __init__(self, needs_refresh=True):
        self.needs_refresh = needs_refresh
        self.shows = 0
        self.quitted = False

    def show(self, timer=None):
        self.shows += 1

    def quit(self):
        self.quitted = True


def _wait(predicate, timeout_s=1.5):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        timer.sleep_ms(5)
    return predicate()


class TestSyncTimers(unittest.TestCase):
    """Tests for synchronous timer backends (machine, librt, win32, sdl2, threading, polling)."""

    def setUp(self):
        self.app = App(timer_async=False)

    def tearDown(self):
        self.app._perform_teardown()

    def test_sync_timer_type(self):
        self.assertFalse(self.app.timer_async)
        self.assertIsNone(self.app._timer)
        self.app.every(20, lambda t: None)
        self.assertIsNotNone(self.app._timer)
        self.assertNotIsInstance(self.app._timer, AsyncTimer)

    def test_sync_timer_periodic_dispatch(self):
        hits = []
        self.app.every(10, lambda t: hits.append(1))
        self.assertTrue(_wait(lambda: len(hits) >= 2), f"Expected >= 2 hits, got {len(hits)}")

    def test_sync_display_auto_refresh(self):
        disp = _FakeDisplay(needs_refresh=True)
        app = App(displays=[disp], timer_async=False)
        self.addCleanup(app._perform_teardown)
        self.assertTrue(_wait(lambda: disp.shows >= 1), "display.show never called in sync mode")

    def test_sync_run_blocking_and_quit(self):
        disp = _FakeDisplay(needs_refresh=True)
        app = App(displays=[disp], timer_async=False)
        self.addCleanup(app._perform_teardown)

        ticks = []

        @app.every(15)
        def on_tick(t):
            ticks.append(len(ticks))
            if len(ticks) >= 3:
                app.request_quit()

        app.run()
        self.assertTrue(app.quit_requested)
        self.assertTrue(disp.quitted)
        self.assertTrue(len(ticks) >= 3)


class TestAsyncTimers(unittest.TestCase):
    """Tests for asynchronous timer backends (AsyncTimer / asyncio)."""

    def test_async_timer_defers_start_until_loop_running(self):
        app = App(timer_async=True)
        self.assertTrue(app.timer_async)
        self.assertIsNone(app._timer)

        hits = []
        app.every(20, hits.append)
        # Timer creation is deferred because event loop is not running yet
        self.assertIsNone(app._timer)
        self.assertTrue(app._deferred)

        # Once the deferred work flushes inside an event loop, the timer starts
        import asyncio

        async def _test():
            app._flush_deferred()
            self.assertIsNotNone(app._timer)
            self.assertIsInstance(app._timer, AsyncTimer)
            # Wait for hits
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                if len(hits) >= 2:
                    return
                await asyncio.sleep(0.02)
            raise AssertionError(f"AsyncTimer never fired, hits: {len(hits)}")

        asyncio.run(_test())
        app._perform_teardown()

    def test_async_display_refresh(self):
        disp = _FakeDisplay(needs_refresh=True)
        app = App(displays=[disp], timer_async=True)
        self.assertIsNone(app._timer)
        self.assertTrue(app._refresh_pending)

        import asyncio

        async def _test():
            app._flush_deferred()
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                if disp.shows >= 1:
                    return
                await asyncio.sleep(0.02)
            raise AssertionError("display.show never called in async mode")

        asyncio.run(_test())
        app._perform_teardown()

    def test_async_run_standalone(self):
        """app.run() in timer_async mode automatically invokes asyncio.run()."""
        disp = _FakeDisplay(needs_refresh=True)
        app = App(displays=[disp], timer_async=True)
        ticks = []

        @app.every(15)
        def on_tick(t):
            ticks.append(len(ticks))
            if len(ticks) >= 3:
                app.request_quit()

        # app.run() handles asyncio loop startup and teardown transparently
        app.run()

        self.assertTrue(app.quit_requested)
        self.assertTrue(disp.quitted)
        self.assertTrue(len(ticks) >= 3, f"Expected >= 3 ticks, got {len(ticks)}")

    def test_async_run_inside_running_loop(self):
        """app.run() inside an existing loop (PyScript/Jupyter) arms and returns."""
        disp = _FakeDisplay(needs_refresh=True)
        app = App(displays=[disp], timer_async=True)
        import asyncio

        async def _host_loop():
            # In an already-running async host (e.g. PyScript / Jupyter), app.run()
            # arms the timer/refresh and returns immediately without blocking.
            app.run()
            self.assertIsNotNone(app._timer)
            self.assertIsInstance(app._timer, AsyncTimer)
            # Host loop ticks along
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                if disp.shows >= 1:
                    break
                await asyncio.sleep(0.02)
            self.assertTrue(disp.shows >= 1)
            app.request_quit()

        asyncio.run(_host_loop())
        app._perform_teardown()


if __name__ == "__main__":
    unittest.main()

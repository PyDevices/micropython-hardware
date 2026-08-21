# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

import os
import runpy
import sys
import threading
import time
import unittest

import _env  # noqa: F401
import multimer
from multimer import (
    AsyncTimer,
    monotonic,
    ticks_add,
    ticks_diff,
    ticks_less,
    ticks_ms,
)
from multimer import auto as timer

Timer = timer.Timer
sleep_ms = timer.sleep_ms

_TICKS_PERIOD = 1 << 29
_TICKS_MAX = _TICKS_PERIOD - 1
_TICKS_HALFPERIOD = _TICKS_PERIOD // 2

_PUBLIC_TIMER_MEMBERS = {"init", "deinit", "ONE_SHOT", "PERIODIC"}


def _public_class_members(cls):
    return {n for n in dir(cls) if not n.startswith("_")}


class TestApiSurface(unittest.TestCase):
    def test_timer_public_members(self):
        self.assertEqual(_public_class_members(Timer), _PUBLIC_TIMER_MEMBERS)

    def test_async_timer_public_members(self):
        self.assertEqual(_public_class_members(AsyncTimer), _PUBLIC_TIMER_MEMBERS)

    def test_constants_match_micropython(self):
        self.assertEqual(Timer.ONE_SHOT, 0)
        self.assertEqual(Timer.PERIODIC, 1)
        self.assertEqual(AsyncTimer.ONE_SHOT, 0)
        self.assertEqual(AsyncTimer.PERIODIC, 1)

    def test_package_exports(self):
        self.assertEqual(
            set(multimer.__all__),
            {
                "AsyncTimer",
                "loop_running",
                "monotonic",
                "run_deadline_hook",
                "schedule",
                "set_deadline_hook",
                "ticks_ms",
                "ticks_add",
                "ticks_diff",
                "ticks_less",
                "asyncio",
            },
        )


class TestProviderSelection(unittest.TestCase):
    def test_root_has_no_timer_or_backend_side_effects(self):
        import subprocess

        code = (
            "import sys; sys.path.insert(0, 'lib'); import multimer; "
            "assert not any(hasattr(multimer, n) for n in ("
            "'Timer','sleep_ms','backends','available_backends',"
            "'backends_available','use_backend')); "
            "assert not any(n in sys.modules for n in ("
            "'multimer.auto','multimer.machine','multimer.librt','multimer.win32',"
            "'multimer.sdl2','multimer.threading','multimer.polling'))"
        )
        subprocess.run([sys.executable, "-c", code], check=True)

    def test_explicit_provider_contract(self):
        from multimer import polling

        self.assertEqual(
            set(polling.__all__),
            {"Timer", "is_async", "name", "pump", "sleep_ms", "uses_interrupts"},
        )
        self.assertEqual(polling.name, "polling")
        self.assertFalse(polling.uses_interrupts)
        self.assertFalse(polling.is_async)
        self.assertEqual(polling.Timer.__module__, "multimer.polling")

    def test_environment_forces_auto_provider_at_import(self):
        import subprocess

        code = (
            "import sys; sys.path.insert(0, 'lib'); "
            "from multimer import auto as timer; "
            "assert timer.name == 'polling'; "
            "assert timer.Timer.__module__ == 'multimer.polling'"
        )
        env = os.environ.copy()
        env["MULTIMER_BACKEND"] = "polling"
        subprocess.run([sys.executable, "-c", code], check=True, env=env)

    def test_environment_can_force_async_auto_provider(self):
        import subprocess

        code = (
            "import sys; sys.path.insert(0, 'lib'); "
            "from multimer import AsyncTimer; from multimer import auto as timer; "
            "assert timer.name == 'async'; assert timer.Timer is AsyncTimer; "
            "assert timer.is_async and not timer.uses_interrupts"
        )
        env = os.environ.copy()
        env["MULTIMER_BACKEND"] = "async"
        subprocess.run([sys.executable, "-c", code], check=True, env=env)

    def test_invalid_environment_backend_fails_without_fallback(self):
        import subprocess

        code = (
            "import sys; sys.path.insert(0, 'lib'); "
            "from multimer import auto"
        )
        env = os.environ.copy()
        env["MULTIMER_BACKEND"] = "no_such_backend"
        result = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown multimer backend", result.stderr)

    def test_auto_matches_provider_contract(self):
        self.assertEqual(
            set(timer.__all__),
            {"Timer", "is_async", "name", "pump", "sleep_ms", "uses_interrupts"},
        )
        self.assertIsInstance(timer.name, str)
        self.assertIsInstance(timer.uses_interrupts, bool)
        self.assertIsInstance(timer.is_async, bool)

    def test_auto_backends_skips_win32_off_windows(self):
        from unittest import mock

        from multimer import auto

        with mock.patch.object(auto.sys, "platform", "linux"):
            self.assertNotIn("win32", auto._auto_backends())

    @unittest.skipUnless(sys.platform == "win32", "win32 timer backend")
    def test_win32_backend_arms(self):
        from multimer import win32

        hits = []
        self.assertTrue(win32.uses_interrupts)
        t = win32.Timer(-1)
        t.init(period=40, callback=lambda _t: hits.append(1))
        try:
            win32.sleep_ms(120)
        finally:
            t.deinit()
        self.assertGreaterEqual(len(hits), 1)

    def test_auto_backends_skips_sdl2_when_pygame_present(self):
        from unittest import mock

        from multimer import auto

        self.assertEqual(sys.implementation.name, "cpython")
        with mock.patch.object(auto, "_pygame_available", return_value=True):
            self.assertNotIn("sdl2", auto._auto_backends())
        # With pygame available, auto-selection must not land on sdl2.
        with mock.patch.object(auto, "_pygame_available", return_value=True):
            # Re-evaluate active backend through the same auto filter used at import.
            candidates = auto._auto_backends()
        self.assertNotIn("sdl2", candidates)

    def test_auto_backends_allows_sdl2_on_cpython_without_pygame(self):
        from unittest import mock

        from multimer import auto

        with mock.patch.object(
            auto, "_pygame_available", return_value=False
        ), mock.patch.object(auto.sys, "platform", "linux"):
            self.assertIn("sdl2", auto._auto_backends())

    def test_auto_backends_skips_sdl2_on_android(self):
        from unittest import mock

        from multimer import auto

        with mock.patch.object(
            auto, "_pygame_available", return_value=False
        ), mock.patch.object(auto.sys, "platform", "android"):
            self.assertNotIn("sdl2", auto._auto_backends())

    def test_async_backend_selects_awaitable_sleep(self):
        from multimer import auto

        provider = auto._load_backend("async")
        self.assertIs(provider.Timer, AsyncTimer)
        self.assertTrue(provider.is_async)
        self.assertFalse(provider.uses_interrupts)
        coro = provider.sleep_ms(0)
        self.addCleanup(coro.close)
        self.assertTrue(hasattr(coro, "send"))

    def test_unknown_backend_raises_value_error(self):
        from multimer import auto

        with self.assertRaises(ValueError):
            auto._load_backend("no_such_backend")

    def test_unavailable_backend_raises_import_error(self):
        # ``machine.Timer`` is absent on CPython desktop; the selection must not
        # fall back silently when a caller asks for a specific backend.
        try:
            from machine import Timer as _MachineTimer  # noqa: F401
        except ImportError:
            pass
        else:
            self.skipTest("machine.Timer is available on this host")
        with self.assertRaises(ImportError):
            from multimer import machine  # noqa: F401

    def test_context_manager_deinits(self):
        hits = []
        from multimer import polling

        with polling.Timer(-1) as t:
            t.init(period=20, callback=lambda _t: hits.append(1))
            for _ in range(8):
                polling.sleep_ms(10)
        self.assertGreaterEqual(len(hits), 1)
        # After exit the timer must be disarmed.
        n = len(hits)
        polling.sleep_ms(50)
        self.assertEqual(len(hits), n)

    def test_provider_constructor_matches_machine_timer_initialization(self):
        from multimer import polling

        hits = []
        timer = polling.Timer(
            -1,
            mode=polling.Timer.ONE_SHOT,
            period=10,
            callback=lambda _timer: hits.append(1),
        )
        try:
            polling.sleep_ms(30)
        finally:
            timer.deinit()
        self.assertEqual(hits, [1])


class TestTicks(unittest.TestCase):
    def test_ticks_ms_in_range(self):
        t = ticks_ms()
        self.assertIsInstance(t, int)
        self.assertGreaterEqual(t, 0)
        self.assertLessEqual(t, _TICKS_MAX)

    def test_monotonic_advances(self):
        start = monotonic()
        self.assertIsInstance(start, (int, float))
        sleep_ms(20)
        self.assertGreaterEqual(monotonic(), start)

    def test_ticks_add_wrap(self):
        self.assertEqual(ticks_add(_TICKS_MAX, 1), 0)

    def test_ticks_add_rejects_ambiguous_intervals(self):
        with self.assertRaises(OverflowError):
            ticks_add(0, _TICKS_HALFPERIOD)
        with self.assertRaises(OverflowError):
            ticks_add(0, -_TICKS_HALFPERIOD)

    def test_host_native_tick_period_is_normalized(self):
        from unittest import mock

        native_add = mock.Mock(return_value=_TICKS_PERIOD)
        native_diff = mock.Mock(return_value=1)
        with mock.patch.object(
            time, "ticks_ms", return_value=_TICKS_PERIOD + 7, create=True
        ), mock.patch.object(
            time, "ticks_add", native_add, create=True
        ), mock.patch.object(
            time, "ticks_diff", native_diff, create=True
        ):
            portable = runpy.run_path(os.path.join(_env.MULTIMER_DIR, "_ticks.py"))

        self.assertEqual(portable["ticks_ms"](), 7)
        self.assertEqual(portable["ticks_add"](_TICKS_MAX, 1), 0)
        self.assertEqual(portable["ticks_diff"](0, _TICKS_MAX), 1)
        native_add.assert_not_called()
        native_diff.assert_not_called()

    def test_ticks_diff_wrap(self):
        later = ticks_add(_TICKS_MAX, 10)
        self.assertEqual(ticks_diff(later, _TICKS_MAX), 10)

    def test_ticks_less(self):
        self.assertTrue(ticks_less(100, 200))

    def test_sleep_ms_advances_time(self):
        start = ticks_ms()
        sleep_ms(50)
        self.assertGreaterEqual(ticks_diff(ticks_ms(), start), 40)


class TestTimerSemantics(unittest.TestCase):
    def test_periodic_fires(self):
        hits = []
        main_thread = threading.get_ident()
        callback_threads = []

        def cb(t):
            hits.append(t)
            callback_threads.append(threading.get_ident())

        t = Timer(-1)
        t.init(period=50, callback=cb)
        for _ in range(35):
            sleep_ms(10)
        t.deinit()
        self.assertGreaterEqual(len(hits), 2)
        self.assertIs(hits[0], t)
        self.assertTrue(callback_threads)
        self.assertEqual(set(callback_threads), {main_thread})

    def test_one_shot_fires_once(self):
        hits = []
        main_thread = threading.get_ident()
        callback_threads = []

        def cb(t):
            hits.append(t)
            callback_threads.append(threading.get_ident())

        t = Timer(-1)
        t.init(mode=Timer.ONE_SHOT, period=50, callback=cb)
        for _ in range(25):
            sleep_ms(10)
        self.assertEqual(len(hits), 1)
        self.assertEqual(callback_threads, [main_thread])

    def test_freq_overrides_period(self):
        hits = []

        t = Timer(-1)
        t.init(freq=20, period=1, callback=lambda _t: hits.append(1))
        for _ in range(25):
            sleep_ms(10)
        t.deinit()
        self.assertGreaterEqual(len(hits), 2)
        self.assertLessEqual(len(hits), 12)

    def test_soft_coalesce_under_threading(self):
        """``hard=False`` must go through ``_deliver`` (coalesce), not raw invoke."""
        try:
            from multimer import threading as thread_timer
        except ImportError:
            self.skipTest("threading backend unavailable")
        hits = []

        def cb(_t):
            hits.append(1)
            thread_timer.sleep_ms(40)

        t = thread_timer.Timer(-1)
        t.init(period=10, callback=cb, hard=False)
        for _ in range(20):
            thread_timer.sleep_ms(10)
        t.deinit()
        # Without coalesce a 10 ms period over ~200 ms would enqueue many more.
        self.assertGreaterEqual(len(hits), 1)
        self.assertLessEqual(len(hits), 8)


class TestSelfDeinit(unittest.TestCase):
    """``deinit()`` from inside a timer's own callback must return, not deadlock.

    ``_deliver()`` holds ``_busy`` for the duration of the callback, and
    ``deinit()`` -> ``_wait_idle()`` used to spin on it, so the delivering thread
    waited on itself forever. ``machine.Timer`` permits self-deinit from an ISR,
    so the software providers must too.

    Delivery is forced onto the ``threading`` provider's worker thread so a
    regression surfaces as a failed deadline rather than hanging the suite.
    """

    def _self_deinit(self, hard):
        try:
            from multimer import threading as thread_timer
        except ImportError:
            self.skipTest("threading backend unavailable")
        done = []
        t = thread_timer.Timer(-1)

        def cb(tim):
            tim.deinit()
            done.append(1)

        t.init(period=10, callback=cb, hard=hard)
        deadline = time.monotonic() + 2.0
        while not done and time.monotonic() < deadline:
            thread_timer.sleep_ms(10)
        self.assertTrue(done, "deinit() from inside the timer's own callback did not return")

    def test_self_deinit_hard(self):
        self._self_deinit(True)

    def test_self_deinit_soft(self):
        self._self_deinit(False)

    def test_wait_idle_returns_while_delivering(self):
        """The reentrancy marker, unit-tested without a live timer."""
        from multimer._core import _TimerCore

        core = _TimerCore.__new__(_TimerCore)
        core._busy = True
        core._delivering = True
        core._wait_idle()  # must return immediately


class TestMpAsyncioShim(unittest.TestCase):
    """``_mpasyncio`` must match the interpreter it borrows ``_asyncio`` from.

    Awaitables: CircuitPython requires ``__await__`` on the operand where
    MicroPython accepts any iterator, and the shim is shared.

    Ticks: due-times land in ``_asyncio.TaskQueue``, a C pairing heap that
    orders them in the interpreter's own ticks domain.
    """

    def setUp(self):
        try:
            from multimer import _mpasyncio
        except ImportError:
            self.skipTest("_mpasyncio unavailable (build ships a real asyncio)")
        self.mod = _mpasyncio

    def test_sleep_is_awaitable(self):
        self.assertTrue(hasattr(self.mod.sleep(0), "__await__"))
        self.mod._sleep_ms_sgen.state = None
        self.assertTrue(hasattr(self.mod.sleep_ms(0), "__await__"))
        self.mod._sleep_ms_sgen.state = None

    def test_event_wait_is_awaitable(self):
        self.assertTrue(hasattr(self.mod.Event().wait(), "__await__"))

    def test_ticks_domain_matches_the_task_queue(self):
        """multimer's ticks_ms masks to 29 bits; time.ticks_ms is 30-bit.

        Handing the C task queue the masked value made every key sort half a
        period away, so tasks were never popped and an AsyncTimer armed under
        this shim never fired.
        """
        native = getattr(time, "ticks_ms", None)
        if native is None:
            self.skipTest("interpreter has no time.ticks_ms")
        self.assertIs(native, self.mod.ticks)


class TestAsyncTimer(unittest.TestCase):
    def test_requires_running_loop(self):
        t = AsyncTimer(-1)
        with self.assertRaises(RuntimeError):
            t.init(period=20, callback=lambda _t: None)

    def test_periodic_under_asyncio(self):
        import asyncio as std_asyncio

        hits = []
        main_thread = threading.get_ident()
        callback_threads = []

        async def main():
            t = AsyncTimer(-1)
            t.init(
                period=20,
                callback=lambda tim: (
                    hits.append(tim),
                    callback_threads.append(threading.get_ident()),
                ),
            )
            await std_asyncio.sleep(0.15)
            t.deinit()

        std_asyncio.run(main())
        self.assertGreaterEqual(len(hits), 2)
        self.assertEqual(set(callback_threads), {main_thread})


class TestLoopRunning(unittest.TestCase):
    def test_false_outside_a_loop(self):
        self.assertFalse(multimer.loop_running())

    def test_true_inside_a_loop(self):
        from multimer import asyncio

        async def main():
            return multimer.loop_running()

        self.assertTrue(asyncio.run(main()))

    def test_ignores_get_event_loop(self):
        """``get_event_loop`` returns a loop even when none runs, so it must not be used.

        A backend offering only ``get_event_loop`` has to report "no loop" rather
        than trusting it — the case that made appdev defer async timers forever
        on MicroPython.
        """
        from multimer import _asyncio_loader

        class OnlyGetEventLoop:
            def get_event_loop(self):
                return "a loop that is not running"

        saved = _asyncio_loader._asyncio_mod
        _asyncio_loader._asyncio_mod = OnlyGetEventLoop()
        try:
            self.assertFalse(_asyncio_loader.loop_running())
        finally:
            _asyncio_loader._asyncio_mod = saved

    def test_prefers_current_task_over_get_running_loop(self):
        """CircuitPython's ``get_running_loop()`` succeeds with no loop running."""
        from multimer import _asyncio_loader

        class LyingGetRunningLoop:
            def current_task(self):
                return None

            def get_running_loop(self):
                return "a loop that is not running"

        saved = _asyncio_loader._asyncio_mod
        _asyncio_loader._asyncio_mod = LyingGetRunningLoop()
        try:
            self.assertFalse(_asyncio_loader.loop_running())
        finally:
            _asyncio_loader._asyncio_mod = saved


class TestSchedule(unittest.TestCase):
    def test_schedule_main_thread(self):
        seen = []
        multimer.schedule(seen.append, 42)
        self.assertEqual(seen, [42])


if __name__ == "__main__":
    unittest.main()

# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""App: application coordinator, event dispatcher, timer manager, and run loop."""

import sys
import events
import keys

from . import _hostloop
from .devices import (
    ENCODER,
    HOST,
    JOYSTICK,
    KEYPAD,
    POINTER,
    Encoder,
    HostEvents,
    Joystick,
    Keypad,
    Touch,
)

DEFAULT_REFRESH_MS = 33
SERVICE_TICK_MS = 10


class _TimerSubscription:
    """Handle for a periodic callback on the App's timer."""

    def __init__(self, app, entry):
        self._app = app
        self._entry = entry

    def cancel(self):
        entry = self._entry
        if entry is None:
            return
        self._entry = None
        entry[3] = True
        try:
            self._app._tick_callbacks.remove(entry)
        except (ValueError, AttributeError):
            pass


class _RefreshClaim:
    def __init__(self, app):
        self._app = app

    def release(self):
        self._app.resume_refresh()


class _RefreshPaused:
    def __init__(self, app):
        self._app = app
        self._claim = None

    def __enter__(self):
        self._claim = self._app.pause_refresh()
        return self._claim

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._claim is not None:
            self._claim.release()
        return False


class App:
    """Application coordinator: devices, shared timer, display refresh, and lifecycle."""

    _current = None
    events = events
    keys = keys
    HOST = HOST
    POINTER = POINTER
    ENCODER = ENCODER
    KEYPAD = KEYPAD
    JOYSTICK = JOYSTICK

    @classmethod
    def current(cls):
        """Return the currently active App instance, or None."""
        return cls._current

    def __init__(
        self,
        board_config=None,
        *,
        displays=None,
        host_read=None,
        touch_read=None,
        touch_rotation_table=None,
        refresh_period=None,
        timer_async=None,
    ):
        App._current = self
        self.devices = []
        self._event_callbacks = {}
        self._tick_callbacks = []
        self._in_tick_dispatch = False
        self._before_quit = None
        self._quit_requested = False
        self._exit_code = None
        self._timer = None

        # Stop timers on any previous App instance to avoid duplicate event dispatch on re-runs
        prev_app = getattr(App, "_current_app", None)
        if prev_app is not None and prev_app is not self:
            try:
                prev_app.stop_timer()
            except Exception:
                pass
        App._current_app = self

        # Work that cannot be armed yet, flushed the moment the loop starts.
        # Replaces the several _pending_* flags that each approximated that
        # moment separately; _hostloop supplies it exactly once.
        self._deferred = []
        self._loop_started = False
        self._strategy = None
        self._refresh_subscription = None
        self._refresh_paused = False
        self._refresh_claim = None
        self._refresh_pending = False
        self._refresh_period = refresh_period
        self._service_subscription = None
        self._service_pending = False
        self._app_drives_poll = False
        self._in_service_poll = False
        self._pending_teardown = False
        self._teardown_done = False
        self._blocking_run = False
        self._ticks_ms = None
        self._ticks_add = None
        self._ticks_diff = None

        self._timer_thread_ident = None
        try:
            if sys.implementation.name == "micropython":
                import _thread

                self._timer_thread_ident = _thread.get_ident()
        except (ImportError, AttributeError):
            pass

        # Parse displays from arguments or board_config
        if displays is not None:
            self._displays = list(displays)
        elif board_config is not None and getattr(board_config, "display_drv", None) is not None:
            self._displays = [board_config.display_drv]
        elif board_config is not None and hasattr(board_config, "width") and hasattr(board_config, "height"):
            self._displays = [board_config]
        else:
            self._displays = []

        for drv in self._displays:
            try:
                drv.app = self
            except Exception:
                pass

        # Determine timer_async
        if timer_async is not None:
            self._timer_async = bool(timer_async)
        elif board_config is not None and hasattr(board_config, "timer_async"):
            self._timer_async = bool(board_config.timer_async)
        else:
            self._timer_async = any(
                getattr(drv, "requires_async_timer", False) for drv in self._displays
            )

        # Wire inputs from board_config or explicit kwargs
        primary = self.primary

        effective_host_read = (
            host_read
            if host_read is not None
            else getattr(board_config, "host_read", None)
            or getattr(board_config, "get_events", None)
        )
        if effective_host_read is not None:
            self.host_dev = HostEvents(host_read=effective_host_read, display=primary)
            self.register(self.host_dev)
        else:
            self.host_dev = None

        effective_touch_read = (
            touch_read if touch_read is not None else getattr(board_config, "touch_read", None)
        )
        effective_touch_table = (
            touch_rotation_table
            if touch_rotation_table is not None
            else getattr(board_config, "touch_rotation_table", None)
        )
        if effective_touch_read is not None:
            self.touch_dev = self.add_touch(
                effective_touch_read,
                display=primary,
                rotation_table=effective_touch_table,
            )
        else:
            self.touch_dev = None

        keypad_read = getattr(board_config, "keypad_read", None)
        if keypad_read is not None:
            self.add_keypad(keypad_read)
        else:
            self.keypad_dev = None

        encoder_read = getattr(board_config, "encoder_read", None)
        if encoder_read is not None:
            self.add_encoder(
                encoder_read,
                button_read=getattr(board_config, "encoder_button_read", None),
            )
        else:
            self.encoder_dev = None

        joystick_driver = getattr(board_config, "joystick_driver", None)
        if joystick_driver is not None:
            emulate_digital = getattr(board_config, "joystick_emulate_digital", None)
            self.add_joystick(joystick_driver=joystick_driver, emulate_digital=emulate_digital)
        else:
            self.joystick_dev = None

        if self._displays:
            self._wire_display_refresh(self._refresh_period)
            self._install_hostloop()

    @property
    def strategy(self):
        """How this app stays alive past the end of the script body.

        One of ``"ambient"`` (the host runs a loop of its own), ``"exit_hook"``
        (an interpreter exit hook takes the main thread), ``"none"`` (nothing
        available -- :meth:`run` is required), or None before wiring.
        """
        return self._strategy

    @property
    def timer_async(self):
        return self._timer_async

    @property
    def displays(self):
        return tuple(self._displays)

    @property
    def primary(self):
        return self._displays[0] if self._displays else None

    @property
    def quit_requested(self):
        return self._quit_requested

    @property
    def before_quit(self):
        return self._before_quit

    @before_quit.setter
    def before_quit(self, value):
        if value is not None and not callable(value):
            raise ValueError("before_quit must be callable")
        self._before_quit = value

    def add_display(self, drv):
        if drv is None:
            raise ValueError("drv is required")
        if drv in self._displays:
            return drv
        first = not self._displays
        self._displays.append(drv)
        try:
            drv.app = self
        except Exception:
            pass
        if first:
            self._wire_display_refresh(self._refresh_period)
            self._install_hostloop()
        elif (
            getattr(drv, "needs_refresh", False)
            and self._refresh_subscription is None
            and not self._refresh_pending
        ):
            self._wire_display_refresh(self._refresh_period)
        return drv

    def remove_display(self, drv):
        if drv not in self._displays:
            return
        was_primary = drv is self.primary
        self._displays.remove(drv)
        try:
            drv.app = None
        except Exception:
            pass
        if callable(getattr(drv, "quit", None)):
            try:
                drv.quit()
            except Exception:
                pass
        elif callable(getattr(drv, "deinit", None)):
            try:
                drv.deinit()
            except Exception:
                pass
        if was_primary or not self._displays:
            self.request_quit()

    def add_touch(self, read, *, display=None, rotation_table=None):
        if display is None:
            display = self.primary
        if display is None:
            raise ValueError("Touch requires a display")
        touch = Touch(read=read, display=display, rotation_table=rotation_table)
        self.register(touch)
        if display is self.primary:
            self.touch_dev = touch
        return touch

    def add_keypad(self, read):
        keypad = Keypad(read=read)
        self.register(keypad)
        self.keypad_dev = keypad
        return keypad

    def add_encoder(self, read, *, button_read=None, button=2):
        encoder = Encoder(read=read, button_read=button_read, button=button)
        self.register(encoder)
        self.encoder_dev = encoder
        return encoder

    def add_joystick(self, joystick_driver, *, emulate_digital=None, digital_threshold=0.5):
        joystick = Joystick(
            joystick_driver=joystick_driver,
            emulate_digital=emulate_digital,
            digital_threshold=digital_threshold,
        )
        self.register(joystick)
        self.joystick_dev = joystick
        return joystick

    def register(self, dev):
        dev.app = self
        if dev not in self.devices:
            self.devices.append(dev)

    def unregister(self, dev):
        if dev in self.devices:
            self.devices.remove(dev)
            dev.app = None

    def on(self, event_type_or_list, callback=None):
        """Subscribe callback to one or more event types, or use as a decorator."""
        if callback is None:
            return lambda fn: self.on(event_type_or_list, fn)
        if not callable(callback):
            raise ValueError("callback must be callable")
        if isinstance(event_type_or_list, (list, tuple, set)):
            for et in event_type_or_list:
                self.on(et, callback)
            return callback
        callback_set = self._event_callbacks.get(event_type_or_list)
        if callback_set is None:
            callback_set = set()
            self._event_callbacks[event_type_or_list] = callback_set
        callback_set.add(callback)
        return callback

    def off(self, event_type_or_list, callback):
        """Unsubscribe callback from one or more event types."""
        if isinstance(event_type_or_list, (list, tuple, set)):
            for et in event_type_or_list:
                self.off(et, callback)
            return
        callback_set = self._event_callbacks.get(event_type_or_list)
        if callback_set:
            callback_set.discard(callback)

    def _ensure_ticks(self):
        if self._ticks_ms is not None:
            return
        from multimer import ticks_add, ticks_diff, ticks_ms

        self._ticks_ms = ticks_ms
        self._ticks_add = ticks_add
        self._ticks_diff = ticks_diff

    @staticmethod
    def _event_loop_running():
        try:
            from multimer import loop_running

            return loop_running()
        except ImportError:
            return False

    def _arm_ready(self):
        """True when a timer can be created right now.

        Async timers need a running event loop (the browser is the exception --
        it owns the loop for the whole program, including import). Some sync
        providers ask to be armed from inside the loop instead of at import.
        """
        if self._timer_async:
            if sys.platform in ("emscripten", "webassembly"):
                return True
            return self._event_loop_running()
        return not self._sync_refresh_needs_deferred_arm()

    def _defer(self, fn):
        """Run ``fn`` now if the app can arm, else at the moment the loop starts."""
        if self._arm_ready():
            fn()
        else:
            self._deferred.append(fn)

    def on_start(self, fn):
        """Register ``fn()`` to run when the app's loop starts.

        Runs immediately if the loop is already able to arm timers. This is the
        single coordination point callers such as ``display_driver`` need in
        place of probing for a running event loop themselves.
        """
        if not callable(fn):
            raise ValueError("fn must be callable")
        self._defer(fn)
        return fn

    def _flush_deferred(self):
        """Arm everything that was waiting for the loop. Called at loop start.

        Only the async gate applies here. A sync provider that sets
        ``_defer_sync_arm`` is asking to be armed *from inside* the loop, which
        is exactly where this runs -- consulting :meth:`_arm_ready` would keep
        deferring forever, since that flag never clears.
        """
        if self._timer_async and not self._arm_ready():
            return
        self._loop_started = True
        while self._deferred:
            self._deferred.pop(0)()

    def _install_hostloop(self):
        """Arrange for the app to outlive the script body. See ``_hostloop``."""
        self._strategy = _hostloop.install(
            pump=self._pump,
            alive=lambda: not self._quit_requested and not self._teardown_done,
            on_start=self._flush_deferred,
            on_stop=self._teardown_from_loop,
            drive=self._drive_async if self._timer_async else None,
        )
        return self._strategy

    def _pump(self):
        from multimer import auto as timer

        timer.sleep_ms(SERVICE_TICK_MS)

    def _drive_async(self):
        from multimer import asyncio

        asyncio.run(self._run_async())

    def every(self, ms=None, callback=None, *, period=None, async_=None):
        """Schedule a periodic callback every ms milliseconds, or use as decorator."""
        if period is not None:
            if callable(ms) and callback is None:
                callback = ms
            ms = period
        if ms is None and period is None:
            ms = 10
        if callback is None:
            if callable(ms):
                callback = ms
                ms = 10
            else:
                return lambda fn: self.every(ms, fn)
        if not callable(callback):
            raise ValueError("callback must be callable")
        self._ensure_ticks()
        if self._timer is None:
            self._defer(lambda: self._start_timer(async_=self._timer_async))
        entry = [callback, int(ms), self._ticks_add(self._ticks_ms(), int(ms)), False]
        self._tick_callbacks.append(entry)
        return _TimerSubscription(self, entry)

    def on_tick(self, callback, period=10, async_=None):
        """Schedule a periodic callback (wrapper around every)."""
        return self.every(period, callback)

    def _start_timer(self, *, async_=False, tick_ms=10):
        if self._timer is not None:
            return self._timer
        # A timer is the other reason an app must outlive the script body, so a
        # display-less app that only schedules callbacks still gets a host loop.
        self._install_hostloop()
        from multimer import AsyncTimer
        from multimer import auto as timer

        self._ensure_ticks()
        timer_class = AsyncTimer if async_ else timer.Timer
        timer_inst = None
        last_err = None
        for timer_id in (-1, 0, 1, 2, 3):
            try:
                timer_inst = timer_class(timer_id)
                break
            except ValueError as exc:
                last_err = exc
        if timer_inst is None:
            raise last_err
        timer_inst.init(
            mode=timer_class.PERIODIC,
            period=tick_ms,
            callback=self._dispatch_tick,
            hard=False,
        )
        self._timer = timer_inst
        return timer_inst

    def stop_timer(self):
        """Stop the shared timer and clear all periodic subscriptions."""
        self._tick_callbacks.clear()
        timer_inst = self._timer
        self._timer = None
        self._refresh_subscription = None
        self._refresh_paused = False
        self._refresh_claim = None
        self._refresh_pending = False
        self._service_subscription = None
        self._service_pending = False
        self._deferred.clear()
        if timer_inst is not None:
            try:
                timer_inst.deinit()
            except Exception:
                # Never let a provider's disarm abort the rest of teardown --
                # displays still have to be released.
                pass

    def _dispatch_tick(self, timer_obj):
        if self._timer_thread_ident is not None:
            try:
                import _thread

                if _thread.get_ident() != self._timer_thread_ident:
                    return
            except (ImportError, AttributeError):
                pass
        if self._in_tick_dispatch:
            return
        self._in_tick_dispatch = True
        try:
            now = self._ticks_ms()
            for entry in tuple(self._tick_callbacks):
                if entry[3]:
                    continue
                if self._ticks_diff(entry[2], now) > 0:
                    continue
                entry[2] = self._ticks_add(now, entry[1])
                entry[0](timer_obj)
            if self._pending_teardown and not self._blocking_run:
                self._try_perform_teardown()
        finally:
            self._in_tick_dispatch = False

    def pause_refresh(self):
        """Pause display refresh while a GUI renders frames."""
        if self._refresh_claim is not None:
            raise RuntimeError("display refresh already claimed/paused")
        self._refresh_paused = True
        self._refresh_claim = _RefreshClaim(self)
        return self._refresh_claim

    def resume_refresh(self):
        """Resume display refresh after pausing."""
        if self._refresh_claim is None:
            return
        self._refresh_paused = False
        self._refresh_claim = None

    def refresh_paused(self):
        """Context manager to pause display refresh within a block."""
        return _RefreshPaused(self)

    def _wire_display_refresh(self, refresh_period):
        if not self._displays:
            return
        self._arm_service()
        needs = any(getattr(d, "needs_refresh", False) for d in self._displays)
        if refresh_period is None:
            wire = needs
            period = DEFAULT_REFRESH_MS
        else:
            refresh_period = int(refresh_period)
            wire = refresh_period > 0
            period = refresh_period if wire else DEFAULT_REFRESH_MS
        if not wire:
            return

        def _show(timer_obj):
            if self._refresh_paused:
                return
            for display in self._displays:
                if getattr(display, "needs_refresh", False) and callable(
                    getattr(display, "show", None)
                ):
                    display.show(timer_obj)

        self._refresh_pending = True
        self._defer(lambda: self._subscribe_refresh(_show, period))

    @staticmethod
    def _sync_refresh_needs_deferred_arm():
        try:
            from multimer import auto as timer

            return getattr(timer, "_defer_sync_arm", False)
        except ImportError:
            return False

    def _subscribe_refresh(self, show_fn, period):
        self._refresh_pending = False
        self._refresh_subscription = self.every(period, show_fn)

    def _arm_service(self):
        if self._service_subscription is not None or self._service_pending:
            return
        self._service_pending = True
        self._defer(self._subscribe_service)

    def _subscribe_service(self):
        self._service_pending = False
        self._service_subscription = self.every(SERVICE_TICK_MS, self._service_tick)

    def _service_tick(self, timer_obj):
        if self._quit_requested or self._app_drives_poll:
            return
        self._in_service_poll = True
        try:
            self.poll()
        finally:
            self._in_service_poll = False

    def poll(self):
        """Poll registered devices and dispatch any pending events."""
        if not self._in_service_poll:
            self._app_drives_poll = True
        try:
            from multimer import run_deadline_hook

            run_deadline_hook()
        except ImportError:
            pass
        try:
            from multimer import auto as timer

            timer.pump()
        except ImportError:
            pass
        self._flush_deferred()

        eventlist = []
        for device in self.devices:
            dev_events = device.poll()
            if dev_events:
                eventlist.extend(dev_events)
                for event in dev_events:
                    if event.type == events.QUIT:
                        self._handle_quit()
                    callbacks = self._event_callbacks.get(event.type)
                    if callbacks:
                        for cb in tuple(callbacks):
                            cb(event)
        return eventlist

    def arm_async_refresh(self):
        """Deprecated alias for flushing deferred arming; prefer :meth:`on_start`.

        Kept because it is public API and callers may still invoke it from
        inside a running loop.
        """
        self._flush_deferred()

    async def _run_async(self, tick_ms=SERVICE_TICK_MS):
        from multimer import asyncio

        self._flush_deferred()
        self._blocking_run = True
        try:
            while not self._quit_requested:
                await asyncio.sleep(tick_ms / 1000)
                try:
                    from multimer import run_deadline_hook

                    run_deadline_hook()
                except ImportError:
                    pass
        finally:
            self._blocking_run = False
        self._perform_teardown()

    def run(self, tick_ms=SERVICE_TICK_MS):
        """Start the application and run until quit."""
        from multimer import auto as timer

        self._install_hostloop()
        _hostloop.claim()

        if self._timer_async:
            if self._event_loop_running():
                self._flush_deferred()
                return
            from multimer import asyncio

            asyncio.run(self._run_async(tick_ms))
            self._raise_exit_code()
            return

        # Nothing to block for when the host already runs a loop and the timer
        # drives itself: an interactive REPL keeps the prompt, and a browser
        # page would deadlock its own event loop if we slept here.
        self_driving = getattr(timer, "uses_interrupts", False) or sys.platform in (
            "emscripten",
            "webassembly",
        )
        if _hostloop.strategy() == _hostloop.AMBIENT and self_driving:
            self._flush_deferred()
            return

        self._flush_deferred()

        self._blocking_run = True
        try:
            while not self._quit_requested:
                timer.sleep_ms(tick_ms)
        finally:
            self._blocking_run = False
            self._perform_teardown()
        self._raise_exit_code()

    def run_async(self, coro_or_fn):
        """Run an async coroutine or factory under the App's async environment."""
        from multimer import asyncio

        if asyncio is None:
            raise RuntimeError("asyncio is not available")

        async def runner():
            self._flush_deferred()
            coro = coro_or_fn() if callable(coro_or_fn) else coro_or_fn
            return await coro

        if self._event_loop_running():
            return asyncio.create_task(runner())
        return asyncio.run(runner())

    def request_quit(self, code=None):
        """Request a clean application shutdown."""
        if code is not None:
            self._exit_code = int(code)
        self._handle_quit()

    def _handle_quit(self):
        if self._quit_requested:
            return
        self._quit_requested = True
        self._refresh_paused = True
        self._pending_teardown = True
        # Single quit choke point. Under ``exit_hook`` the loop notices via
        # ``alive()``; under ``ambient`` nothing of ours would ever notice, so
        # ``quit()`` performs teardown there. Both land on _teardown_from_loop.
        _hostloop.quit()
        if self._in_service_poll:
            self._teardown_from_loop()

    def _teardown_from_loop(self):
        """Tear down, deferring one turn if we are inside a callback."""
        if self._teardown_done:
            return
        if (self._in_service_poll or self._in_tick_dispatch) and self._schedule_async_teardown():
            return
        self._perform_teardown()

    def _schedule_async_teardown(self):
        """Defer teardown to the next loop turn. True when scheduled.

        Not gated on ``timer_async``: ``multimer.auto`` resolves to an async
        provider in the browser even for an app that never asked for one, and
        deinitialising an async-backed timer from inside its own callback fails
        with "can't cancel self". Whether a loop is running is the question, and
        ``create_task`` answers it.
        """
        try:
            from multimer import asyncio

            async def _later():
                await asyncio.sleep(0)
                self._perform_teardown()

            asyncio.create_task(_later())
            return True
        except Exception:
            return False

    def _try_perform_teardown(self):
        # Reached from inside _dispatch_tick, so it must take the deferring
        # path: tearing down there cancels the very task/timer delivering the
        # callback ("can't cancel self" on an AsyncTimer).
        self._teardown_from_loop()

    def _perform_teardown(self):
        if self._teardown_done:
            return
        self._teardown_done = True
        self._quit_requested = True
        if App._current is self:
            App._current = None
        self._pending_teardown = False
        if self._before_quit is not None:
            try:
                self._before_quit()
            except Exception:
                pass
        self.stop_timer()
        for display in tuple(self._displays):
            if callable(getattr(display, "quit", None)):
                try:
                    display.quit()
                except Exception:
                    pass
        self._displays.clear()

    def _raise_exit_code(self):
        code = self._exit_code
        if code is not None:
            self._exit_code = None
            raise SystemExit(code)

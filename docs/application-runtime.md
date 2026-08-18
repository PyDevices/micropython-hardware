# Runtime and board config

Every application needs a `board_config.py` on `sys.path` that describes its
hardware or host. The board config exports hardware capabilities; the
application decides which coordinator, if any, to instantiate.

## Board-config contract

| Symbol | Required | Role |
|---|---|---|
| `display_drv` | yes for display apps | Display interface from `displaydev` |
| `host_read` | hosted input only | Callable that returns host events |
| `touch_read` | touch boards only | Callable that returns contact points |
| `touch_rotation_table` | optional | Four rotation masks for touch coordinates |
| `keypad_read` | optional | Keypad reader |
| `encoder_read` / `encoder_button_read` | optional | Encoder readers |
| `joystick_driver` / `emulate` | optional | Joystick input and optional emulation mapping |
| `timer_async` | optional | Host preference for async timing |

Board configs do not import `eventsys` and do not export `runtime`.

## Standard applications

Applications opt into the optional event traffic controller by instantiating the coordinator directly:

```python
import board_config
from board_config import display_drv
import eventsys

runtime = eventsys.Runtime.from_board_config(board_config)

runtime.run_forever()
```

Reusable `eventsys` remains independent of board hardware details.

You may also provide overrides:

```python
runtime = eventsys.Runtime.from_board_config(
    board_config,
    refresh_period=16,
    timer_async=True,
)
```

## LVGL applications

LVGL supplies its own coordinator:

```python
from display_driver import runtime
```

That implementation bridges LVGL to `displaydev` and `multimer`, owns LVGL
tick/task handling and input-device adapters, and does not import `eventsys`.

## Direct constructor

```python
eventsys.Runtime(
    display=None,
    host_read=None,
    touch_read=None,
    touch_rotation_table=None,
    refresh_period=None,
    timer_async=False,
)
```

Bare `Runtime()` is valid for custom wiring. Additional devices can be attached
after construction:

```python
runtime.add_keypad(read=buttons.read)
runtime.add_joystick(joystick_driver=drv)
runtime.add_encoder(read=pos_read, button_read=btn_read, button=2)
```

## App loop & `run_forever()`

The supplied coordinator can manage the application loop:

```python
def on_click(event):
    ...

runtime.on(runtime.events.MOUSEBUTTONDOWN, on_click)
runtime.run_forever()
```

### How `runtime.run_forever()` Behaves

`runtime.run_forever()` automatically adapts its behavior based on the runtime environment and timer model:

1. **Interactive REPL (`python -i`, `micropython -i`, MCU prompt)**:
   - When running with hardware interrupts or signal-based timers (`machine.Timer`, Linux `librt`, Windows `uwin32`), `run_forever()` **immediately returns**.
   - The interactive prompt (`>>>`) stays open for live debugging and introspection while the UI continues running and responding to inputs in the background.

2. **Standalone Desktop CLI (`python app.py`)**:
   - In non-interactive desktop scripts, `run_forever()` **sleeps in a keep-alive loop** until a quit event occurs.
   - This prevents the desktop OS process from exiting immediately after drawing the initial window.

3. **Async / Cooperative / Pumped Modes (`asyncio`, CircuitPython, Browser)**:
   - `run_forever()` runs the event loop continuously to pump timer ticks and process queued events.

Or an application can explicitly poll:

```python
while not runtime.quit_requested:
    for event in runtime.poll():
        handle(event)
    draw_frame()
```

Hosted displays that set `needs_refresh` are presented by the coordinator.
Display-only MCU applications can omit `eventsys` entirely and call
`display_drv.show()` according to their own policy.


## `timer_async`

Board configs publish a neutral `timer_async` preference. Current defaults are:

| Host | Value |
|---|---|
| PyScript / Jupyter | `True` |
| PG/SDL desktop | `False`, optionally overridden by `PYDEVICES_TIMER_ASYNC` |
| MCU board config | selected by that config |

Examples do not read the environment variable directly. The selected
coordinator consumes `board_config.timer_async`; test harnesses can use their
`--timer-async` option.

## Touch read contract

`touch_read` is called once per poll. It returns either a falsy value for no
contacts or a sequence of `(x, y[, id[, …]])` contacts. The runtime maps the
primary contact to mouse-style events and exposes all rotated contacts as
`runtime.touch_dev.points`.

| Return value | Meaning |
|---|---|
| `None`, `()`, or `[]` | no touch; releases an active press |
| sequence of point tuples | current contacts |
| legacy bare `(x, y[, …])` | one contact; supported for compatibility |

Coordinates are panel/pre-rotation coordinates. `touch_rotation_table` maps
them to the active display rotation. New drivers should prefer `read_points()`
returning a sequence, even for one contact.

## Refresh ownership

A GUI layer that presents frames itself can pause eventsys-driven refresh:

```python
with runtime.display_refresh_paused():
    run_game()
```

LVGL does not use this eventsys mechanism: its own coordinator owns presentation
from the outset.

## Quit lifecycle

On `QUIT`, eventsys runs its optional `before_quit` hook, releases the display,
and stops its timer. `runtime.quit_requested` remains true after the first quit.

See [Events](eventsys.md), [Architecture](architecture.md), and
[Board configs](https://pydevices.github.io/pydevices/board-configs.html).

## Background work on MicroPython (`_thread`)

On ESP32, MicroPython worker threads (`_thread` / `mp_thread`) get a very small
stack. Do **not** run network I/O, discovery, or other deep call stacks on a new
thread spawned from a soft timer or an input callback — that overflows the stack
(`Stack protection fault` in task `mp_thread`).

Queue the work and run it on the main tick instead: `eventsys.Runtime.on_tick`,
an LVGL `lv.timer`, or a soft [`multimer.auto.Timer`](multimer.md) pump. Keep UI
mutations on that same main path. Desktop CPython can still use threads freely —
this constraint is specific to MCU MicroPython.

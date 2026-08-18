# eventsys

Optional cross-platform event traffic controller for applications using PyGame/SDL2-style events. It unifies touch, mouse, keyboard, keypad, encoder, and joystick input under one app-owned `Runtime`.

`eventsys` is not part of a board definition and is not required by LVGL. Board configs expose hardware and read callables; a non-LVGL app can choose `eventsys`, provide another coordinator, or handle those devices directly.

## Install

### CPython (TestPyPI)

This package is published as a pure-Python wheel to TestPyPI.

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pydevices-eventsys
```

Why both indexes: [two-index pip install](https://github.com/PyDevices/pydevices/blob/main/docs/publishing.md).

Pulls in `pydevices-multimer` for shared timers used by `Runtime`, plus `pydevices-events` and `pydevices-keys`. Python imports remain `multimer`, `events`, and `keys`.

### MicroPython (MIP)

```python
import mip

mip.install("eventsys", index="https://PyDevices.github.io/mip")
```

## Quick start

```python
import events
import eventsys
import board_config

runtime = eventsys.Runtime.from_board_config(board_config)

while True:
    for event in runtime.poll():
        if event.type == events.KEYDOWN:
            print("down", event.key)
        elif event.type == events.QUIT:
            break
```

Or subscribe instead of polling — `runtime.on(events.KEYDOWN, handler)` then
`runtime.run_forever()`.

**Devices, mappers, the async model, and `from_board_config` wiring are in
[docs/eventsys.md](https://github.com/PyDevices/pydevices/blob/main/docs/eventsys.md).**

## What you get

- `Runtime` — an optional app-level traffic controller with poll / subscribe, display refresh wiring, and sync/async keep-alive
- Devices: `TouchDevice`, `KeypadDevice`, `EncoderDevice`, `JoystickDevice`, `HostEventsDevice`
- Optional mappers: `eventsys.touch_keypad`, `eventsys.joystick_keys`
- Event types/key codes: install `pydevices-events` and `pydevices-keys` (`import events`, `import keys`)

## Links

- [Documentation — eventsys](https://github.com/PyDevices/pydevices/blob/main/docs/eventsys.md)
- [Documentation — Runtime](https://github.com/PyDevices/pydevices/blob/main/docs/application-runtime.md)
- [Source](https://github.com/PyDevices/pydevices)
- [Issues](https://github.com/PyDevices/pydevices/issues)
- Related TestPyPI distributions: `pydevices-events`, `pydevices-keys`, `pydevices-multimer`, `pydevices-displaydev`

## License

MIT — see [LICENSE](https://github.com/PyDevices/pydevices/blob/main/LICENSE).

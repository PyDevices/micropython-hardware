# Architecture

`pydevices` is the core product layer, owning portable hardware interfaces, driver abstractions, board wiring contracts, and releases.

Applications build directly on the **PyDevices Board Contract** and core packages (`displaydev`, `audiodev`, `eventsys`, `multimer`). Downstream showcases like `pydevices-examples` consume this layer as companion sample code.

## Component diagram

```mermaid
flowchart TB
  subgraph product [pydevices Core Engine]
    BC[board_config.py - Eager UI Hardware]
    BP[board_peripherals.py / boarddev - Lazy Extras]
    DD[displaydev - Display Abstraction]
    AD[audiodev - Audio Abstraction]
    EV[events and keys]
    MT[multimer - Portable Timers]
    ES[eventsys - Optional Event Dispatcher]
    DR[Hardware & Bus Drivers]
  end
  subgraph app [Application / GUI Layer]
    APP[Custom Application / User GUI]
    AR[eventsys.Runtime / App Loop]
    LR[display_driver - LVGL Coordinator]
  end
  subgraph showcase [Companion Showcase]
    EX[pydevices-examples Gallery & Demos]
  end

  DR --> BC
  BC --> DD
  BC --> AD
  BC -.-> BP
  EV --> ES
  MT --> ES

  BC --> APP
  DD --> APP
  BP --> APP

  BC --> AR
  ES --> AR
  BC --> LR
  MT --> LR

  APP --> EX
  AR --> EX
  LR --> EX
```

## Core Responsibilities

| Piece | Role |
|---|---|
| `board_config.py` | Primary Board Contract: initializes eager UI hardware (`display_drv`, touch, buttons) and exports neutral capability flags. |
| `board_peripherals.py` / `boarddev` | Board Contract extension: provides lazy, on-demand access to extra hardware (sensors, battery monitors, external storage). |
| `displaydev` | Cross-platform display interfaces (`BusDisplay`, `FBDisplay`, `SDLDisplay`, `PyScriptDisplay`). |
| `audiodev` | Cross-platform audio output/input interfaces (`I2SAudio`, `SDLAudio`). |
| `events` / `keys` | Neutral event definitions, key codes, modifier keys, and touch gestures. |
| `multimer` | Cross-platform timing primitives (explicit `Timer` providers, optional `auto`, `AsyncTimer`, and ticks). |
| `eventsys` | Optional event traffic controller and input queue for applications using native PyDevices dispatch. |
| `display_driver` | LVGL coordinator bridging LVGL widgets to `displaydev` and `multimer`. |

## Standard Application Boot Sequence

1. Install `pydevices` or your board's `board_config` via MIP or pip.
2. Import `display_drv` from `board_config`.
3. Draw directly or bind your choice of UI toolkit (`pdwidgets`, `lvgl`, or raw framebuffers).
4. Run your application event loop.

```python
from board_config import display_drv

# Draw to the display hardware
display_drv.fill_rect(0, 0, 100, 50, 0xF800)
display_drv.show()
```

## Where to go next

- [Board Contract Specification](board-peripherals.md) — eager vs lazy board hardware
- [Board Config Inventory](board-configs.md) — supported MCU & desktop boards
- [Display Drivers](displaydev.md) — display interfaces and backends
- [multimer](multimer.md) — portable timers and async support
- [Companion Demos](https://pydevices.github.io/pydevices-examples/) — sample applications

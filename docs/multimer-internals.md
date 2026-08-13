# Timer backend internals & platform capabilities

This document explains the internal architecture of `multimer`: how platform backends are selected, the underlying C-binding and threading capabilities of each Python runtime, and how PyDevices bridges hardware interrupts, OS signals, and SDL2 event pumps.

For the general user guide and quickstart, see [multimer](multimer.md). For display driver integration, see [Display backend internals](displaydev-internals.md) and [Runtime](application-runtime.md).

---

## Platform capabilities matrix

The table below details the underlying system capabilities available to `multimer` across all supported runtimes:

| Runtime / Executable | Target Platform | FFI / C-Bindings | Threading Support | SDL2 Provider | Signal / Interrupt Timers | Default `multimer` Backend |
|---|---|---|---|---|---|---|
| **CPython** (`python`) | Linux Desktop | `ctypes` | Full `threading` + `_thread` | `usdl2.py` (via `ctypes`) or `pygame` | POSIX real-time signals (`librt`) | `librt` (`uses_signals=True`) |
| **MicroPython** (`micropython`) | Linux Unix port | `ffi` + `uctypes` | Built-in `_thread` | `usdl2.py` (via `ffi`) | POSIX real-time signals (`librt`) | `librt` (`uses_signals=True`) |
| **CircuitPython** (`circuitpython`) | Linux port | None | Built-in `_thread` | `displayif` (compiled C module) | None | `sdl2` / `polling` (`uses_signals=False`) |
| **CPython** (`python.exe`) | Windows | `ctypes` | Full `threading` + `_thread` | `usdl2.py` (via `ctypes`) or `pygame-ce` | Waitable Timer APCs (`uwin32.py`) | `win32` (`uses_signals=True`) |
| **MicroPython** (`micropython.exe`) | Windows Win32 port | None (planned in `cmods`) | None | `displayif` (compiled C module) | None | `sdl2` / `polling` (`uses_signals=False`) |
| **CPython** (`python`) | Android | `ctypes` | Full `threading` + `_thread` | `pygame` / native Android surface | None | `threading` (`uses_signals=False`) |
| **MicroPython** | MCU Boards | None / Native C | Port-dependent `_thread` | N/A (Direct panel bus) | Hardware interrupts (`machine.Timer`) | `machine` (`uses_signals=True`) |
| **CircuitPython** | MCU Boards | None | None | N/A (Direct panel bus) | None | `polling` (`uses_signals=False`) |

| **PyScript / Pyodide** | Browser / WASM | `js` / `pyodide` FFI | None (single-threaded WASM) | HTML5 Canvas | Browser host loop / Web APIs | `async` / host loop (`uses_signals=False`) |

---

## How SDL2 is bridged (`usdl2.py` vs `displayif`)

Hosted desktop and simulation targets often use SDL2 for window management, frame presentation, and input polling. PyDevices provides two distinct mechanisms to connect to SDL2 depending on the host's FFI capabilities:

### 1. Pure-Python FFI Bridge (`usdl2.py`)
When running on **CPython** (Linux/Windows) or **MicroPython Unix** (Linux), the runtime has access to dynamic foreign function interfaces (`ctypes` or `ffi`):
* `usdl2.py` dynamically loads the system `libSDL2.so` or `SDL2.dll` at runtime.
* No C compilation or custom binary build is needed.
* Timer ticks and window pump hooks can be called directly from Python code.

### 2. Compiled User C Module (`displayif` / `cmods`)
When running on runtimes **without FFI** (such as `micropython.exe` or `circuitpython`):
* Python cannot load DLLs or shared libraries dynamically.
* The [cmods](https://github.com/PyDevices/cmods) workspace compiles `displayif` directly into the interpreter binary as a native C module (`usdl2`).
* Python code imports `usdl2` as a built-in module, exposing identical SDL function signatures without requiring runtime FFI.

---

## Signal & Interrupt Timer Delivery

Timers marked with `uses_signals() == True` deliver callbacks directly to the main thread in the background. This eliminates the need for an application-level sleep pump and enables the **Interactive REPL** debugging workflow.

### 1. Linux `librt` (POSIX Signals)
* Uses `timer_create` and `timer_settime` with `SIGEV_THREAD_ID` targeting the main thread.
* On CPython, signal handlers are registered via `signal.signal()`.
* On MicroPython Unix, signal handlers use `ffi` and `uctypes`.
* When a timer expires, the kernel interrupts execution on the main thread and runs the Python callback immediately.

### 2. Windows `uwin32.py` (Alertable APCs)
* Uses `CreateWaitableTimerExW` and `SetWaitableTimer` with completion APCs (`TIMERAPCROUTINE`).
* When the main thread enters an **alertable wait state** (via `SleepEx(..., alertable=True)` in `multimer.sleep_ms()`, or console I/O read in `python.exe -i`), the Windows kernel delivers the queued APC to the main thread.
* This provides signal-like background execution on Windows without spinning worker threads.

### 3. Microcontroller `machine.Timer` (Hardware Interrupts)
* On MicroPython boards (ESP32, RP2040, STM32, etc.), `machine.Timer` is backed directly by hardware timer peripherals and ISRs.
* Callbacks are scheduled via `micropython.schedule()`, executing safely on the main VM thread between bytecodes.

---

## MicroPython & CircuitPython Roadmap Considerations

### `micropython.exe` (Windows)
Currently, `micropython.exe` lacks both FFI and threading support. As a result:
* It cannot execute `uwin32.py` or Win32 waitable timers.
* It relies on `displayif` for SDL2 windowing and uses pumped sleep loops.
* **Roadmap**: A planned patch in `cmods` will enable FFI on `micropython.exe`, unlocking `uwin32.py` and alertable APC hardware timer parity with `python.exe`.

### CircuitPython
CircuitPython intentionally omits `machine.Timer` and low-level FFI in favor of high-level board abstractions and cooperative `asyncio`. Applications running on CircuitPython boards or the Linux port always use `multimer.AsyncTimer` or active sleep-pump loops.

# AGENTS.md — micropython-hardware

Sibling of [pydisplay](https://github.com/PyDevices/pydisplay). Owns
**board configs**, **hardware drivers**, and their **MIP package manifests**.
Docs are markdown under `docs/`, published only via GitHub Pages
([pydevices.github.io/micropython-hardware](https://pydevices.github.io/micropython-hardware/))
— not Read the Docs. Build locally with `./scripts/build_pages.sh` (needs
`pandoc`).

## Do

- Add/edit MicroPython boards under `board_configs/` and CircuitPython under
  `board_configs/cp/` (same directory names as MicroPython; do not add an `mp/`
  mirror). Chip helpers under `drivers/` (see `drivers/README.md`).
- Keep shared bus/touch/chip MIP manifests under `packages/` (`spibus.json`,
  `sdcard.json`, …). MicroPython board dirs get a `package.json`; do **not**
  add `package.json` under `board_configs/cp/`.
- Prefer vendored single-file drivers (micropython-lib / reputable GitHub) for
  shared chips. Use `machine.SDCard` for SDMMC/SDIO and `sdcard.py` for SPI CS
  paths.
- **MicroPython** board devices contract: `board_config.py` (eager UI) +
  `board_devices.py` (`DEVICES`, lazy factories) + `setup_devices(globals())`
  using pydisplay `boarddev`. Pin wiring for lazy extras lives in
  `board_devices` factories.
- **CircuitPython** (`board_configs/cp/`): **no** `board_devices.py`, **no**
  `DEVICES` / `setup_devices`, and **no** `from board_config import …`.
  CircuitPython already has the native `board` module for pins/buses. CP
  `board_config.py` only provides `display_drv`, `runtime`, and eager input
  devices that wire into `runtime` (`touch`, `keypad`, `encoder`, `joystick`)
  using contract names. Non-UI peripherals stay on CP `board` / libraries.
- Keep MIP `package.json` URLs on
  `github:PyDevices/micropython-hardware/...` for files in this repo.
  Pull `boarddev.py` from `github:PyDevices/pydisplay/src/lib/boarddev.py`
  (MicroPython boards only).
  Pull pydisplay core deps (`displaysys`, …) from
  `github:PyDevices/pydisplay/packages/...`.

## Do not

- Re-introduce pure-Python core libraries here (`displaysys`, `eventsys`, …).
- Commit large generated assets unrelated to boards/drivers.
- Rename the GitHub repo casually — MIP URLs and docs pin this name.
- Add `board_devices.py` under `board_configs/cp/`.

## Local layout

Typical clone: `~/gh/pydevices/micropython-hardware` next to
`~/gh/pydevices/pydisplay`.

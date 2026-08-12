# AGENTS.md — pydevices

Canonical PyDevices product/source repository. Owns **board configs**,
**hardware drivers**, portable libraries (`displaydev`, `audiodev`, optional
`eventsys`, `multimer`, `events`, `keys`), and pip/MIP publishing.
Docs are markdown under `docs/`, published only via GitHub Pages
([pydevices.github.io/pydevices](https://pydevices.github.io/pydevices/))
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
- **MicroPython** board devices contract: `board_config.py` (eager UI hardware) +
  `board_devices.py` (`DEVICES`, lazy factories) + `setup_devices(globals())`
  using the product-owned `boarddev`. Pin wiring for lazy extras lives in
  `board_devices` factories.
- **CircuitPython** (`board_configs/cp/`): **no** `board_devices.py`, **no**
  `DEVICES` / `setup_devices`, and **no** `from board_config import …`.
  CircuitPython already has the native `board` module for pins/buses. CP
  `board_config.py` provides `display_drv`, eager input hardware, and neutral
  read aliases (`touch_read`, `keypad_read`, `encoder_read`, and so on). Board
  configs never instantiate `eventsys` or an application runtime. Non-UI
  peripherals stay on CP `board` / libraries.
- Run `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests` after changing `displaydev`, `multimer`, `events`, `keys`, `audiodev`, `boarddev`, or `utils/`. See `tests/README.md`.
- Keep MIP `package.json` URLs on
  `github:PyDevices/pydevices/...` for files in this repo,
  including `boarddev.py`, which is localized under `drivers/boarddev.py`
  (MicroPython boards only; all sources are product-owned).
  MIP names and Python imports remain unprefixed (`displaydev`, `audiodev`,
  `eventsys`, `events`, `keys`, `multimer`). TestPyPI distribution names are
  always `pydevices-*`. `displaydev` → `events` + `keys`; optional `eventsys`
  → `events` + `keys` + `multimer`. Board `package.json` never depends on
  `eventsys`; the application installs it when selected. GitHub package
  manifests live under `packages/`.
  Portable `utils/` (`byteswap`, `mip`, `viper_tools`, `keypins`, `wifi`,
  `frame_recorder`, CPython `micropython` shim) is installed via
  `packages/utils.json`.
  `AutoDisplay` is `displaydev.auto` only — never re-exported from
  `displaydev/__init__.py`. Backends must not import `.auto`.

## Do not

- Put product libraries or their release pipeline back in the examples repo.
- Instantiate `eventsys.Runtime` (or any traffic controller) in a board config.
- Import `displaydev.auto` from `displaydev/__init__.py` or any backend.
- Commit large generated assets unrelated to boards/drivers.
- Rename the GitHub repo casually — MIP URLs and docs pin this name.
- Add `board_devices.py` under `board_configs/cp/`.

## Local layout

Typical clone: `~/gh/pydevices/pydevices` next to
`~/gh/pydevices/pydevices-examples`.

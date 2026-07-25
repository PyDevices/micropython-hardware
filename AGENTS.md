# AGENTS.md — micropython-hardware

Sibling of [pydisplay](https://github.com/PyDevices/pydisplay). Owns
**board configs**, **hardware drivers**, and their **MIP package manifests**.
Pages site: [pydevices.github.io/micropython-hardware](https://pydevices.github.io/micropython-hardware/)
(`web/` + `device-matrix.md`). Inventory / fixture / bring-up notes live under
`docs/`.

## Do

- Add/edit boards under `board_configs/` and chip helpers under `drivers/`.
- Keep shared bus/touch/chip MIP manifests under `packages/` (`spibus.json`, …).
- Prefer the board devices contract for new or graduating boards:
  `board_config.py` (eager UI) + `board_devices.py` (`DEVICES`, lazy factories)
  + `setup_devices(globals())` using pydisplay `boarddev`.
- Keep MIP `package.json` URLs on
  `github:PyDevices/micropython-hardware/...` for files in this repo.
  Pull `boarddev.py` from `github:PyDevices/pydisplay/src/lib/boarddev.py`.
  Pull pydisplay core deps (`displaysys`, …) from
  `github:PyDevices/pydisplay/packages/...`.

## Do not

- Re-introduce pure-Python core libraries here (`displaysys`, `eventsys`, …).
- Commit large generated assets unrelated to boards/drivers.
- Rename the GitHub repo casually — MIP URLs and docs pin this name.

## Local layout

Typical clone: `~/gh/pydevices/micropython-hardware` next to
`~/gh/pydevices/pydisplay`.

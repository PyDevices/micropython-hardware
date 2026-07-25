# Device matrix

Campaign boards in this repo use the [board devices contract](board-devices.md):
eager UI in `board_config.py`, lazy extras in `board_devices.py` (`DEVICES`).

Related inventories (keep concerns separate):

| Doc | Role |
|-----|------|
| [board-inventory.md](docs/board-inventory.md) | Physical Detect fixtures (#) — chip, flash, runtime |
| [firmware-fixtures.md](docs/firmware-fixtures.md) | Detect probe notes / esptool details |
| [pydisplay-display-boards.md](docs/pydisplay-display-boards.md) | Display bring-up quirks (panel, touch, soft-reset) |
| **This file** | Fixture # ↔ product ↔ `board_config` ↔ eager / lazy roles |

Paths below are relative to `board_configs/`.

---

## Campaign matrix

| Product | Inventory # | `board_config` path | Eager UI | Lazy `DEVICES` |
|---------|-------------|---------------------|----------|----------------|
| Waveshare ESP32-P4-WIFI6-Touch-LCD-4B | [#1](docs/board-inventory.md) | `fbdisplay/esp32-p4-wifi6-touch-lcd-4b` | `touch` | `audio`, `microphone`, `sdcard`, `camera`, `ethernet`, `radio`, `wlan`, `ble`, `usb_device` |
| Adafruit Qualia S3 + TL040HDS20 | [#8](docs/board-inventory.md) | `fbdisplay/qualia_tl040hds20` | `touch`, `keypad`, `io_expander` | `wlan`, `ble` |
| Waveshare ESP32-S3-Touch-LCD-4.3 | — | `fbdisplay/esp32-s3-touch-lcd-4_3` | `touch`, `io_expander` | `sdcard`, `can`, `rs485`, `usb_device`, `wlan`, `ble` |
| Waveshare ESP32-S3-Touch-LCD-7 | — | `fbdisplay/esp32-s3-touch-lcd-7` | `touch`, `io_expander` | `sdcard`, `can`, `rs485`, `usb_device`, `wlan`, `ble` |
| LILYGO T-RGB 2.1″ | — | `fbdisplay/t-rgb_480` | `touch` | `sdcard`, `battery`, `wlan`, `ble` |
| LILYGO T-Embed | — | `busdisplay/spi/t-embed` | `encoder` | `pixels`, `audio`, `microphone`, `sdcard`, `battery`, `i2c`, `wlan`, `ble` |
| LILYGO T-HMI | — | `busdisplay/i80/t-hmi` | `touch` | `sdcard`, `i2c`, `wlan`, `ble` |
| Waveshare RP2040-Touch-LCD-1.28 | — | `busdisplay/spi/rp2040-touch-lcd-1.28` | `touch` | `accelerometer`, `gyroscope`, `battery` |
| Adafruit Metro M7 + TFT shield 1947 | — | `busdisplay/spi/metro_m7_tft_touch_shield_1947` | `touch` | `pixels`, `led`, `sdcard`, `radio`, `wlan`, `i2c` |
| ST NUCLEO-H743ZI2 + TFT shield 1947 | [#25](docs/board-inventory.md) | `busdisplay/spi/nucleo_h743zi2_tft_touch_shield_1947` | `touch` | `led`, `sdcard`, `ethernet` |

`display_drv` / `runtime` / `display_bus` are always part of the board surface
when present; they are omitted from the Eager column for brevity.

---

## MIP install

```python
import mip
mip.install(
    "github:PyDevices/micropython-hardware/board_configs/<path>"
)
```

Replace `<path>` with a directory from the table (for example
`fbdisplay/esp32-p4-wifi6-touch-lcd-4b`). Also install pydisplay core packages
listed in that board’s `package.json` `deps`.

---

## Notes

- Lazy roles listed in `DEVICES` may still raise `NotImplementedError` until
  factories are filled in — the set is the contract surface, not a completeness
  guarantee.
- Boards without an Inventory # are on-hand for display bring-up but were not
  part of the 2026-07-18 Detect fixture capture.
- `bt` (Classic) is omitted; none of these campaign boards expose it.

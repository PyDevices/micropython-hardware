# Device matrix

Campaign and product boards in this repo use the
[board devices contract](board-devices.md): eager UI in `board_config.py`, lazy
extras in `board_devices.py` (`DEVICES`).

Related inventories (keep concerns separate):

| Doc | Role |
|-----|------|
| [board-inventory.md](board-inventory.md) | Physical Detect fixtures (#) — chip, flash, runtime |
| [firmware-fixtures.md](firmware-fixtures.md) | Detect probe notes / esptool details |
| [pydisplay-display-boards.md](pydisplay-display-boards.md) | Display bring-up quirks (panel, touch, soft-reset) |
| **This file** | Fixture # ↔ product ↔ `board_config` ↔ eager / lazy roles |

Paths below are relative to `board_configs/` and are **MicroPython** trees only.
CircuitPython twins under `cp/` are deferred (not listed as retrofit targets).

---

## Campaign matrix

First-wave display campaign. Lazy column is the live `DEVICES` set.

| Product | Inventory # | `board_config` path | Eager UI | Lazy `DEVICES` |
|---------|-------------|---------------------|----------|----------------|
| Waveshare ESP32-P4-WIFI6-Touch-LCD-4B | [#1](board-inventory.md) | `fbdisplay/esp32-p4-wifi6-touch-lcd-4b` | `touch` | `audio`, `microphone`, `sdcard`, `camera`, `ethernet`, `radio`, `wlan`, `ble`, `usb_device` |
| Adafruit Qualia S3 + TL040HDS20 | [#8](board-inventory.md) | `fbdisplay/qualia_tl040hds20` | `touch`, `keypad`, `io_expander` | `wlan`, `ble` |
| Waveshare ESP32-S3-Touch-LCD-4.3 | — | `fbdisplay/esp32-s3-touch-lcd-4_3` | `touch`, `io_expander` | `sdcard`, `can`, `rs485`, `usb_device`, `wlan`, `ble` |
| Waveshare ESP32-S3-Touch-LCD-7 | — | `fbdisplay/esp32-s3-touch-lcd-7` | `touch`, `io_expander` | `sdcard`, `can`, `rs485`, `usb_device`, `wlan`, `ble` |
| LILYGO T-RGB 2.1″ | — | `fbdisplay/t-rgb_480` | `touch` | `sdcard`, `battery`, `wlan`, `ble` |
| LILYGO T-Embed | — | `busdisplay/spi/t-embed` | `encoder` | `pixels`, `audio`, `microphone`, `sdcard`, `battery`, `i2c`, `wlan`, `ble` |
| LILYGO T-HMI | — | `busdisplay/i80/t-hmi` | `touch` | `sdcard`, `i2c`, `wlan`, `ble` |
| Waveshare RP2040-Touch-LCD-1.28 | — | `busdisplay/spi/rp2040-touch-lcd-1.28` | `touch` | `accelerometer`, `gyroscope`, `battery` |
| Adafruit Metro M7 + TFT shield 1947 | [#5](board-inventory.md) host | `busdisplay/spi/metro_m7_tft_touch_shield_1947` | `touch` | `pixels`, `led`, `sdcard`, `radio`, `wlan`, `i2c` |
| ST NUCLEO-H743ZI2 + TFT shield 1947 | [#25](board-inventory.md) | `busdisplay/spi/nucleo_h743zi2_tft_touch_shield_1947` | `touch` | `led`, `sdcard`, `ethernet` |

`display_drv` / `runtime` / `display_bus` are always part of the board surface
when present; they are omitted from the Eager column for brevity.

---

## Product matrix (MP retrofit)

Sensor-rich / inventory-linked products. All rows below have
`board_devices.py` unless noted. Some factories still raise
`NotImplementedError` until chip drivers land — the `DEVICES` set is the
contract surface.

| Product | Inventory # | `board_config` path (MP) | Eager UI | Lazy `DEVICES` | Notes |
|---------|-------------|--------------------------|----------|----------------|-------|
| Adafruit FunHouse | [#13](board-inventory.md) | `busdisplay/spi/funhouse` | `touch`, `keypad` | `temperature`, `humidity`, `pressure`, `pixels`, `audio`, `wlan` | no BLE on ESP32-S2 |
| Adafruit PyGamer | [#27](board-inventory.md) | `busdisplay/spi/pygamer` | `joystick`, `keypad` | `pixels`, `accelerometer`, `sdcard`, `battery`, `audio`, `i2c` | |
| Adafruit Feather RP2040 + RGB matrix wing | [#7](board-inventory.md) host | `fbdisplay/feather_rp2040_rgb_matrix_64x32` | — | `i2c` | matrix is `display_drv` |
| Adafruit Feather RP2040 DVI | [#21](board-inventory.md) | — (CP only) | — | — | CP POC under `cp/fbdisplay/adafruit_feather_rp2040_dvi_320x240`; no MP `board_config` yet |
| Teensy 4.1 + FlexIO ILI9341 | [#23](board-inventory.md) | `busdisplay/i80/teensy41_flexio_ili9341` | — | *(empty)* | split layout; no onboard lazy extras |
| Teensy 4.1 + RGB matrix featherwing | [#23](board-inventory.md) | `fbdisplay/rgb_matrix_featherwing_teensy41_64x32` | — | *(empty)* | |
| Adafruit MagTag | — | `epaperdisplay/magtag` | `keypad` | `pixels`, `audio`, `i2c`, `wlan` | no contract role for ALS |
| Adafruit CLUE | — | `busdisplay/spi/clue` | `keypad` | `accelerometer`, `gyroscope`, `magnetometer`, `temperature`, `humidity`, `pressure`, `microphone`, `pixels`, `led`, `i2c`, `ble` | BMP280/pixels/led/i2c/ble live; IMU/humidity/mic raise |
| Adafruit PyBadge | — | `busdisplay/spi/pybadge` | `keypad` | `pixels`, `accelerometer`, `audio`, `i2c` | |
| Adafruit PyPortal | — | `busdisplay/spi/pyportal` | `touch` | `sdcard`, `radio`, `audio`, `i2c`, `wlan` | AirLift as `radio`/`wlan` |
| Adafruit PyPortal Titano | — | `busdisplay/spi/pyportal_titano` | `touch` | `sdcard`, `radio`, `audio`, `i2c`, `wlan` | |
| Adafruit HalloWing M4 | — | `busdisplay/spi/hallowing_m4` | — | `pixels`, `accelerometer`, `audio`, `i2c` | |
| ODROID-GO | — | `busdisplay/spi/odroid_go` | `joystick`, `keypad` | `battery`, `sdcard`, `audio`, `wlan` | |
| M5Stack CoreS3 | — | `busdisplay/spi/m5stack-cores3` | `touch` | `microphone`, `audio`, `sdcard`, `camera`, `accelerometer`, `gyroscope`, `i2c`, `wlan`, `ble` | several factories raise until codecs/IMU land |
| M5Stack Tab5 (ILI9881C) | — | `fbdisplay/m5stack_tab5_ili9881c` | `touch` | `microphone`, `audio`, `sdcard`, `camera`, `i2c`, `wlan`, `ble` | same |
| M5Stack Tab5 (ST7123) | — | `fbdisplay/m5stack_tab5_st7123` | `touch` | `microphone`, `audio`, `sdcard`, `camera`, `i2c`, `wlan`, `ble` | same |
| LILYGO T-Display-S3 | — | `busdisplay/i80/t-display-s3` | — | `battery`, `wlan`, `ble` | |
| LILYGO T-Display-S3 Pro | — | `busdisplay/spi/t-display-s3-pro` | `touch` | `sdcard`, `battery`, `wlan`, `ble` | |
| LILYGO T-QT Pro | — | `busdisplay/spi/t-qt-pro` | — | `battery`, `wlan`, `ble` | |
| LILYGO T-Dongle-S3 | — | `busdisplay/spi/t-dongle-s3` | — | `pixels`, `wlan`, `ble` | |
| Adafruit MatrixPortal M4 | — | `fbdisplay/matrixportal_m4_64x32` | — | `accelerometer`, `i2c` | HUB75 is `display_drv` |
| Adafruit MatrixPortal S3 | — | `fbdisplay/matrixportal_s3_64x64` | — | `accelerometer`, `i2c`, `wlan`, `ble` | |
| BPI-Centi-S3 | — | `busdisplay/i80/bpi-centi-s3` | `encoder` | `wlan`, `ble` | |
| WT32-SC01 Plus | — | `busdisplay/i80/wt32sc01-plus` | `touch` | `sdcard`, `wlan`, `ble` | |
| ESP32-WROVER-E ST7789 + joystick | — | `busdisplay/spi/esp32_wrover_e_st7789_joystick` | `joystick` | `wlan` | |
| PiTFT ILI9341 FeatherWing | — | `busdisplay/spi/pitft_ili9341_featherwing` | `touch` | `i2c` | host-dependent STEMMA |

### Inventory fixtures without a product `board_config`

Detect capture only — no dedicated pydisplay product config to retrofit.
Shield / host rows above already cover Metro M7 (#5) and Nucleo (#25) with
display shields.

| # | Board / model | Notes |
|---|---------------|-------|
| 2–4, 6, 9–10, 12, 14–15, 22 | Generic ESP32-S3 modules | No product display config |
| 11 | Waveshare RP2040-Plus | No product display config (distinct from RP2040-Touch-LCD-1.28) |
| 16 | Raspberry Pi Pico | Host only; use sock / shield configs when applicable |
| 17, 20, 28 | ESP32-PICO-V3-02 boards | No product display config |
| 18 | Adafruit QT Py M0 | No onboard display config (EyeSPI stacks are separate) |
| 19 | Seeed XIAO nRF52840 Sense | Sensors on-hand; no display `board_config` |
| 24 | SparkFun Thing Plus SAMD51 | No product display config |
| 26 | Adafruit PyRuler | No display |
| 29 | Adafruit Feather nRF52840 Express | Host only |
| 30 | Adafruit Trinket M0 | No display |

---

## MIP install

```python
import mip
mip.install(
    "github:PyDevices/micropython-hardware/board_configs/<path>"
)
```

Replace `<path>` with a directory from the tables (for example
`fbdisplay/esp32-p4-wifi6-touch-lcd-4b`). Also install pydisplay core packages
listed in that board’s `package.json` `deps`.

---

## Notes

- Lazy roles listed in `DEVICES` may still raise `NotImplementedError` until
  factories are filled — the set is the contract surface, not a completeness
  guarantee.
- Boards without an Inventory # were not part of the 2026-07-18 Detect fixture
  capture (or are common products kept for the matrix).
- `bt` (Classic) is omitted unless a product is known to expose BR/EDR.
- Light / ALS sensors have no contract role yet — omit from `DEVICES`.
- Metro M7 inventory [#5](board-inventory.md) is the host; the campaign path is
  the host + Adafruit TFT shield 1947.
- Generic epaper/OLED breakouts and EyeSPI stacks are not enumerated here unless
  they expose meaningful non-display `DEVICES` roles.

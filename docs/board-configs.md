# Board configs

Every pydisplay app needs a `board_config.py` that wires up the display, input devices, and optional [Runtime](https://pydisplay.readthedocs.io/en/latest/concepts/runtime/).

For the stable end-device role names (`touch`, `wlan`, …), lazy `DEVICES`
discovery, and the touch duck-type, see **[Board devices](board-devices.md)**.

## What board_config.py provides

Typically:

- A `display_drv` object (BusDisplay, SDLDisplay, PGDisplay, FBDisplay, etc.)
- A `runtime` object (`eventsys.Runtime(...)`) when the display needs periodic present or input dispatch; `None` on MCU display-only boards
- Optional input devices wired into `runtime` (e.g. `touch`, `keypad`, `encoder`, `joystick`)
- Optional setup (backlight pins, buses). On **MicroPython**, lazy extras move
  to `board_devices` under the [board devices contract](board-devices.md). On
  **CircuitPython**, there is no `board_devices` — use the native `board`
  module for non-UI peripherals.

Configs live in
[`PyDevices/micropython-hardware`](https://github.com/PyDevices/micropython-hardware)
(`board_configs/`). Each MicroPython directory with a `package.json` can be installed via MIP:

See the canonical commands and verification steps in
[install-workflows.md](install-workflows.md).

Standard MCU pattern: install the matching `board_config` directory and let
`package.json` dependencies resolve automatically from the PyDevices MIP index.

CircuitPython configs live under `board_configs/cp/` with the same bus layout and
directory names as MicroPython (no `cp_` prefix, no `package.json` / MIP, no
`board_devices.py`). MicroPython configs stay at the top level of
`board_configs/` (not under an `mp/` folder).

## Picking a config

Match in priority order:

1. **Bus type** — SPI vs I80 (parallel)
2. **Display controller** — ILI9341, ST7789, GC9A01, …
3. **Touch controller** — FT6X36, XPT2046, …
4. **Microcontroller** — ESP32-S3, RP2040, …

An exact match for all four is rare; bus + display controller is usually enough to adapt.

## SPI bus configs

| Directory | Hardware |
|-----------|----------|
| `busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3` | Wokwi ESP32-S3 + ILI9341 + touch |
| `busdisplay/spi/wokwi_ili9341_esp32s3_no_touch` | Wokwi ESP32-S3 + ILI9341 |
| `busdisplay/spi/t-display-s3-pro` | LilyGO T-Display S3 Pro |
| `busdisplay/spi/t-display-s3` | (I80 variant under `i80/t-display-s3`) |
| `busdisplay/spi/t-dongle-s3` | LilyGO T-Dongle S3 |
| `busdisplay/spi/t-embed` | LilyGO T-Embed |
| `busdisplay/spi/t-qt-pro` | LilyGO T-QT Pro |
| `busdisplay/spi/m5stack-cores3` | M5Stack CoreS3 |
| `busdisplay/spi/wt32sc01-plus` | (I80 under `i80/wt32sc01-plus`) |
| `busdisplay/spi/ili9341_eyespi_qtpy_esp32s3` | Adafruit ESP32-S3 QT Py + EyeSPI ILI9341 |
| `busdisplay/spi/ili9341_eyespi_qtpy_rp2040` | QT Py RP2040 + EyeSPI ILI9341 |
| `busdisplay/spi/ili9341_pico_uno` | Pico + UNO-style shield |
| `busdisplay/spi/diy_esp32_ili9341_xpt2046` | DIY ESP32 + ILI9341 + XPT2046 |
| `busdisplay/spi/esp32_wrover_e_st7789_joystick` | ESP32 WROVER-E + ST7789 + joystick |
| `busdisplay/spi/seeed_gc9a01_on_qtpy_esp32s3` | GC9A01 round display on QT Py ESP32-S3 |
| `busdisplay/spi/seeed_gc9a01_on_qtpy_rp2040` | GC9A01 on QT Py RP2040 |
| `busdisplay/spi/pico-lcd-1.8` | Pico LCD 1.8" |
| `busdisplay/spi/rp2040-touch-lcd-1.28` | RP2040 1.28" round LCD |
| `busdisplay/spi/odroid_go` | ODROID-GO |

## I80 (parallel) bus configs

| Directory | Hardware |
|-----------|----------|
| `busdisplay/i80/t-display-s3` | LilyGO T-Display S3 |
| `busdisplay/i80/t-hmi` | LilyGO T-HMI |
| `busdisplay/i80/wt32sc01-plus` | Sunton WT32-SC01 Plus |
| `busdisplay/i80/ili9341_i80_rp2040` | RP2040 + ILI9341 I80 |
| `busdisplay/i80/bpi-centi-s3` | BPI Centi-S3 |

## Framebuffer / special configs

| Directory | Hardware |
|-----------|----------|
| `fbdisplay/qualia_tl040hds20` | MicroPython Qualia RGB |
| `fbdisplay/esp32-p4-wifi6-touch-lcd-4b` | Waveshare ESP32-P4-WIFI6-Touch-LCD-4B (MIPI-DSI, touch, ES8311; [TTS UIs](audio.md#speech)) |
| `fbdisplay/t-rgb_480` | LilyGO T-RGB 480×480 ST7701 (ESP32-S3; RGB via pydevices/displayif) |
| `fbdisplay/pico2_dvi_sock_640x480` | Pico 2 + Adafruit DVI Sock or PiCowbell HSTX |
| `fbdisplay/pico2w_dvi_sock_640x480` | Pico 2 W + Sock / PiCowbell HSTX |
| `fbdisplay/olimex_rp2350pc_640x480` | Olimex RP2350pc onboard HDMI (HSTX) |
| `fbdisplay/sparkfun_iot_redboard_rp2350_hstx_640x480` | SparkFun IoT RedBoard + HSTX→DVI breakout + FPC |
| `fbdisplay/adafruit_metro_rp2350_hstx_640x480` | Metro RP2350 + Adafruit HSTX→DVI adapter |
| `cp/fbdisplay/qualia_tl040hds20` | CircuitPython Qualia |
| `cp/fbdisplay/usb_video` | CircuitPython USB Video |
| `cp/fbdisplay/matrixportal_s3_64x64` | MatrixPortal S3 HUB75 64×64 |
| `fbdisplay/matrixportal_s3_64x64` | MP skeleton (rgbmatrix cmod) |

## Pixel / addressable LED configs

| Directory | Hardware |
|-----------|----------|
| `cp/pixeldisplay/neopixel_8x4` | NeoPixel 8×4 grid (CircuitPython) |
| `pixeldisplay/neopixel_8x4` | NeoPixel 8×4 grid (MicroPython) |
| `cp/pixeldisplay/dotstar_12x6` | DotStar 12×6 grid (CircuitPython) |
| `pixeldisplay/dotstar_12x6` | DotStar 12×6 grid (MicroPython) |

Draw through `display_drv` only; `_pixel_framebuf` is an internal wiring detail.

## E-paper configs

| Directory | Hardware |
|-----------|----------|
| `cp/epaperdisplay/magtag` | Adafruit MagTag SSD1680 + KEYPAD |
| `epaperdisplay/magtag` | MagTag SSD1680 + KEYPAD (MP) |
| `cp/epaperdisplay/ssd1680_213_featherwing` | 2.13" E-Ink FeatherWing |
| `epaperdisplay/ssd1680_213_featherwing` | 2.13" E-Ink FeatherWing (MP) |
| `cp/epaperdisplay/acep7in_73` | ACeP 7.3" 7-color E-Ink |
| `epaperdisplay/acep7in_73` | ACeP 7.3" (MP) |
| `cp/epaperdisplay/ssd1675_213_featherwing` | SSD1675 2.13" monochrome FeatherWing |
| `epaperdisplay/ssd1675_213_featherwing` | SSD1675 2.13" FeatherWing (MP) |
| `cp/epaperdisplay/uc8151d_29_breakout` | UC8151D 2.9" flexible breakout |
| `epaperdisplay/uc8151d_29_breakout` | UC8151D 2.9" breakout (MP) |

Additional vendored chip drivers (each has a CircuitPython sibling under `cp/epaperdisplay/`): `ssd1681_154_tricolor`, `ssd1683_213_featherwing`, `ssd1677_583_mono`, `ssd1608_154_mono`, `il0373_213_tricolor`, `il0398_42_mono`, `il91874_27_tricolor`, `uc8179_583_mono`, `uc8253_37_mono`, `ek79686_27_tricolor`, `jd79661_213_4gray`, `jd79667_391_4gray`, `spd1656_154_acep`.

Tri-color / 4-gray configs use `color_depth=2` (0=white, 1=black, 2=accent). ACeP configs use `color_depth=4`.

| Directory | Hardware |
|-----------|----------|
| `cp/fbdisplay/matrixportal_m4_64x32` | MatrixPortal M4 HUB75 64×32 |
| `cp/busdisplay/spi/hallowing_m4` | HalloWing M4 |
| `cp/busdisplay/spi/pyportal_titano` | PyPortal Titano + touch |
| `cp/busdisplay/i2c/sh1107_oled_128x64` | SH1107 OLED |
| `cp/busdisplay/spi/ssd1351_128_oled` | SSD1351 color OLED |

## I2C OLED configs

| Directory | Hardware |
|-----------|----------|
| `cp/busdisplay/i2c/ssd1306_oled_featherwing` | FeatherWing OLED 128×32 |
| `busdisplay/i2c/ssd1306_oled_featherwing` | FeatherWing OLED 128×32 (MP + `i2cbus`) |
| `busdisplay/i2c/sh1107_oled_128x64` | SH1107 OLED 128×64 (MP + `i2cbus`) |

## Built-in Adafruit boards (SPI)

| Directory | Hardware |
|-----------|----------|
| `cp/busdisplay/spi/pyportal` | PyPortal + TT21100 touch |
| `busdisplay/spi/pyportal` | PyPortal + TT21100 (MP SAMD51) |
| `cp/busdisplay/spi/pyportal_titano` | PyPortal Titano + touch |
| `busdisplay/spi/pyportal_titano` | PyPortal Titano (MP SAMD51) |
| `cp/busdisplay/spi/funhouse` | FunHouse ST7789 + touch |
| `busdisplay/spi/funhouse` | FunHouse ST7789 + TT21100 (MP ESP32-S2) |
| `cp/busdisplay/spi/pybadge` | PyBadge LC + buttons |
| `busdisplay/spi/pybadge` | PyBadge LC + shift-register KEYPAD (MP) |
| `cp/busdisplay/spi/hallowing_m4` | HalloWing M4 |
| `busdisplay/spi/hallowing_m4` | HalloWing M4 ST7735 (MP) |
| `cp/busdisplay/spi/pitft_ili9341_featherwing` | PiTFT FeatherWing + STMPE610 |
| `busdisplay/spi/pitft_ili9341_featherwing` | PiTFT FeatherWing (MP Feather + STMPE610) |
| `cp/busdisplay/spi/funhouse` | FunHouse ST7789 + touch |
| `cp/busdisplay/spi/pygamer` | PyGamer ST7789 |
| `busdisplay/spi/pygamer` | PyGamer ST7789 (MP SAMD51) |
| `cp/busdisplay/spi/pitft_ili9341_featherwing` | PiTFT FeatherWing + STMPE610 |
| `cp/busdisplay/spi/ssd1331_096_oled` | SSD1331 color OLED |
| `busdisplay/spi/ssd1331_096_oled` | SSD1331 color OLED (MP) |
| `cp/busdisplay/spi/ssd1351_128_oled` | SSD1351 color OLED |
| `busdisplay/spi/ssd1351_128_oled` | SSD1351 color OLED (MP) |
| `cp/busdisplay/i80/t-display-s3` | LilyGO T-Display S3 I80 |
| `cp/busdisplay/i80/t-hmi` | LilyGO T-HMI I80 + touch |
| `cp/busdisplay/i80/wt32sc01-plus` | WT32-SC01 Plus I80 |
| `cp/busdisplay/spi/*` | CircuitPython variants of MP configs |

## Desktop / browser configs

| Directory | Platform |
|-----------|----------|
| `sdldisplay` | CPython / MicroPython Unix — SDL2 (`SDLDisplay`) |
| `sdldisplay/linux_kms` | Linux KMS/DRM (no X11/Wayland) — `SDL_VIDEODRIVER=kmsdrm` |
| `pgdisplay` | CPython — PyGame (`PGDisplay`) |
| `jndisplay` | Jupyter Notebook |
| `psdisplay` | PyScript browser |

## Default config

[`board_configs/desktop/`](../board_configs/desktop/) — universal non-MCU
`board_config` for desktop, PyScript, and Jupyter. Host display selection is
`displaysys.AutoDisplay` (PS / JN / PG→SDL); the config itself is MCU-shaped
eager wiring (`display_drv` + `runtime` + `setup_devices`).

| Branch | `runtime.timer_async` |
|--------|------------------------|
| PyScript | `True` (asyncio-native host) |
| Jupyter | `True` (ipyevents / kernel loop) |
| PG/SDL desktop | `False` unless **`PYDISPLAY_TIMER_ASYNC`** is set |

Panel size overrides (before `import board_config`): `PYDISPLAY_WIDTH`,
`PYDISPLAY_HEIGHT`, `PYDISPLAY_ROTATION`, `PYDISPLAY_SCALE`. Apps should read
geometry from `display_drv`, not module-level names on `board_config`.

Set the env var **before** `import board_config` (or any import that loads it).
Truthy: `1`, `true`, `yes`, `on`. Falsey: `0`, `false`, `no`, `off`. Unknown
values fall back to the desktop default (`False`). Parsing lives in
[`displaysys.env_bool`](https://github.com/PyDevices/pydisplay/blob/main/src/lib/displaysys/__init__.py).

```bash
# Force asyncio timers on desktop (LVGL async smoke, matrix column)
PYDISPLAY_TIMER_ASYNC=1 python my_example.py
```

Per-board configs under `board_configs/` pass `timer_async=` explicitly in
their `Runtime(...)` call; they do not read this env var unless you wire it in.

## Custom config

Copy the closest match, edit pin assignments and driver imports, and test with `import pydisplay_demo`. See the [**pydisplay_demo** guide](../examples/pydisplay_demo.md) for a walkthrough of the recommended smoke test.

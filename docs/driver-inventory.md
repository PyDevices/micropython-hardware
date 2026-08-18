# Driver inventory

Status of display and touch drivers vendored into PyDevices from Adafruit and community bundles.

## SPI / I80 TFT (BusDisplay)

| File | Source | Status |
|------|--------|--------|
| `gc9a01.py` | Adafruit GC9A01A | in repo |
| `gc9d01.py` | Adafruit / community | in repo |
| `hx8357.py` | Adafruit | in repo |
| `ili9163.py` | Adafruit / Electronut | in repo |
| `ili9341.py` | Adafruit | in repo |
| `ili9488.py` | Adafruit | in repo |
| `st7735.py` | Adafruit | in repo |
| `st7735r.py` | Adafruit | in repo |
| `st7735r_1.py` | variant | in repo |
| `st7789.py` | Adafruit | in repo |
| `st7789vw.py` | variant | in repo |
| `st7796.py` | Adafruit | in repo |
| `st7701.py` | LilyGO T-RGB | in repo (`run_init` + `t-rgb_480` board config; pixel bus via displayif `rgbframebuffer`) |
| `ra8875.py` | Adafruit | skipped (framebuf API, not displayio) |

## OLED (BusDisplay)

| File | Source | Status |
|------|--------|--------|
| `sh1106.py` | Adafruit DisplayIO | vendored |
| `sh1107.py` | Adafruit DisplayIO | vendored |
| `ssd1305.py` | Adafruit DisplayIO | vendored |
| `ssd1306.py` | Adafruit DisplayIO | vendored |
| `ssd1322.py` | Adafruit | vendored |
| `ssd1325.py` | Adafruit | vendored |
| `ssd1327.py` | Adafruit | vendored |
| `ssd1331.py` | Adafruit | vendored |
| `ssd1351.py` | Adafruit | vendored |

## Other

| File | Source | Status |
|------|--------|--------|
| `pcd8544.py` | Adafruit | vendored |
| `community/st7565.py` | Community DisplayIO | vendored |
## Input

| File | Source | Status |
|------|--------|--------|
| `keypad_gpio.py` | PyDevices | in repo |
| `keypad_shift.py` | PyDevices (74HC165) | in repo |

## Touch

| File | Source | Status |
|------|--------|--------|
| `ft6x36.py` | PyDevices MP | in repo |
| `tt21100.py` | PyDevices MP | in repo |
| `stmpe610.py` | PyDevices MP (SPI) | in repo |
| `xpt2046.py` | PyDevices MP | in repo |
| `gt911.py` | PyDevices MP | in repo |
| `cst8xx.py` | PyDevices MP | in repo |
| `cst226.py` | PyDevices MP | in repo |
| `chsc6x.py` | PyDevices MP | in repo |
| `circuitpython/adafruit_focaltouch.py` | Adafruit shim | in repo |
| `circuitpython/adafruit_ft5336.py` | Adafruit | vendored |
| `circuitpython/adafruit_tsc2007.py` | Adafruit | vendored |
| `circuitpython/adafruit_tt21100.py` | Adafruit | vendored |
| `circuitpython/adafruit_stmpe610.py` | Adafruit | vendored |
| `circuitpython/adafruit_touchscreen.py` | Adafruit 4-wire | vendored |

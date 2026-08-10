# Drivers

Hardware helpers for [micropython-hardware](https://github.com/PyDevices/micropython-hardware)
board configs. Prefer single-file modules; MIP manifests live under `../packages/`.

| Path | Role |
|------|------|
| `storage/sdcard.py` | SPI SD block device ([micropython-lib](https://github.com/micropython/micropython-lib)) |
| `imu/qmi8658.py` | 6-axis IMU |
| `imu/lis3dh.py` | ST LIS3DH accelerometer (PyGamer / PyBadge) |
| `imu/bmi270.py` | Bosch BMI270 IMU (CoreS3; from micropython-lib) |
| `env/ahtx0.py` | AHT10/AHT20 humidity + temperature |
| `env/bmp280.py` | BMP280 pressure + temperature ([dafvid/micropython-bmp280](https://github.com/dafvid/micropython-bmp280)) |
| `led/dotstar.py` | APA102 / DotStar ([mattytrentini/micropython-dotstar](https://github.com/mattytrentini/micropython-dotstar)) |
| `codec/es8311.py` | ES8311 DAC/ADC init for I2S |
| `codec/es7210.py` | Minimal ES7210 ADC init for I2S mics (`profile="m5"` for CoreS3/Tab5) |
| `codec/aw88298.py` | AW88298 smart amp init (CoreS3) |
| `codec/es8388.py` | ES8388 DAC init (Tab5) |
| `audio/sdl2audio.py` | SDL2 queued PCM for `audiodev` (needs `usdl2`) |
| `usdl2.py` | Pure-Python SDL2 ctypes/ffi binding for desktop SDL |
| `audio/pygameaudio.py` | pygame-ce PCM backend |
| `audio/webaudio.py` | PyScript / Web Audio backend |
| `audio/audiodev.py` | Portable `AudioFormat` / PCM device contracts |
| `power/battery_adc.py` | ADC + divider → volts |
| `bus/rs485.py` | UART (+ optional DE) |
| `bus/canbus.py` | `machine.CAN` helper when firmware exposes TWAI |
| `bus/`, `touch/`, `display/`, `io_expander/`, `input/`, `joystick/` | Existing display/touch/bus helpers |

Use `machine.SDCard` for SDMMC/SDIO slots; use `sdcard.py` for SPI CS paths.

The audio backends share a stream contract and carry host-specific workarounds
that are easy to undo by accident — read [`audio/README.md`](audio/README.md)
before changing them.

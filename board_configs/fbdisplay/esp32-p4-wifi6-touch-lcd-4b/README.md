# Waveshare ESP32-P4-WIFI6-Touch-LCD-4B

MIP board package for pydisplay (`board_config` + `board_devices`) with
MIPI-DSI FBDisplay, touch, and ES8311 `audio_out` / `audio_in`.

## TTS UIs

| Setup script | Example | Secrets |
|--------------|---------|---------|
| `setup_tts_kokoro.py` | [`tts_kokoro`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tts_kokoro.py) | `KOKORO_BASE_URL` |
| `setup_tts_gemini.py` | [`tts_gemini`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tts_gemini.py) | `GEMINI_API_KEY` |
| `setup_tts_orpheus.py` | [`tts_orpheus`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tts_orpheus.py) | `ORPHEUS_BASE_URL` |

Host / networking details:
https://pydevices.github.io/micropython-hardware/audio.html

### Prerequisites

1. Firmware with frozen **lvgl**, **display_driver**, **mipidsi** / display stack, and **requests** (TLS for Gemini).
2. On the board filesystem:

   | Path | Purpose |
   |------|---------|
   | `/wifi.py` | Connect helper (`connect_from_secrets`) |
   | `/secrets.py` | WiFi + provider keys/URLs (see below) |

Example `/secrets.py` fields (include what you need):

```python
WIFI_SSID = "your-ssid"
WIFI_PASSWORD = "your-password"
# Kokoro — LAN IP of the PC running uvicorn --http h11 on :8880
KOKORO_BASE_URL = "http://192.168.1.10:8880/v1"
# Gemini
GEMINI_API_KEY = "…"
# Orpheus — LAN IP of the FastAPI bridge (LM Studio GGUF + bridge on :5005)
ORPHEUS_BASE_URL = "http://192.168.1.10:5005/v1"
```

### Install (WiFi up)

```python
import mip
# Kokoro (local):
mip.install(
    "github:PyDevices/micropython-hardware/board_configs/fbdisplay/"
    "esp32-p4-wifi6-touch-lcd-4b/setup_tts_kokoro.py",
    target="/",
)
import setup_tts_kokoro
# Or: setup_tts_gemini / setup_tts_orpheus
```

Each script installs the board package, `tts`, and the chosen UI under `/lib`,
and writes `/main.py` to connect WiFi then import that UI.

### Launch

MicroPython soft-reset skips `main.py`. Use **soft-reboot** (`Ctrl-D`) or a
hard reset. Or from the REPL after WiFi: `import tts_kokoro` (or
`tts_gemini` / `tts_orpheus`).

### Files installed

| Path | Role |
|------|------|
| `/lib/board_config.py` | Display + lazy `DEVICES` |
| `/lib/board_devices.py` | `audio_out`, etc. |
| `/lib/tts.py` | Provider adapters + `TTSClient` |
| `/lib/tts_*.py` | Chosen LVGL UI |
| `/main.py` | WiFi → selected UI |

# Portable audio

The audio surface is split by direction: boards expose `audio_out` and/or
`audio_in`. Each object owns stream lifecycle and reports an `AudioFormat` plus
a `capabilities` set. PCM output supports `write`, `drain`, `awrite`, and
`adrain`; PCM input supports `readinto` and `areadinto`. Volume, gain, and mute
use a normalized 0–100 scale and select hardware controls when a codec provides
them, otherwise `audiodev` scales PCM in software.

Codec-specific features remain reachable through `device.codec`. Shared
half-duplex hardware uses `AudioSession`; opening the opposite direction while
one direction owns the session raises `OSError`.

## Host backends

`sdl2audio.py` is the reference playback and real-microphone backend for
MicroPython and CPython. It uses queued SDL audio and provides the same sync and
async contract as hardware devices. `pygameaudio.py` provides CPython playback,
primarily for pygame-ce applications on Windows. pygame-ce has no public capture
API, so applications use `sdl2audio.audio_in` for host microphones.

## Speech

The SAM example synthesizes locally and writes its PCM directly to an
`audio_out` device. [`drivers/audio/tts.py`](../drivers/audio/tts.py) supplies
optional streaming HTTP adapters and sends provider-neutral PCM chunks through
the same `audio_out` contract (`TTSClient.speak` / `.stream`).

| Provider class | Typical use | Default format |
|----------------|-------------|----------------|
| `KokoroTTS` | Local Kokoro-82M OpenAI-compatible server | streamed PCM 24 kHz |
| `OrpheusTTS` | Local Orpheus via LM Studio + FastAPI bridge | WAV → PCM |
| `OpenAITTS` | OpenAI `/v1/audio/speech` | PCM |
| `ElevenLabsTTS` | ElevenLabs stream | PCM |
| `AzureTTS` | Azure Cognitive Services | PCM |
| `GoogleTTS` | Google Cloud TTS | WAV-in-JSON |
| `GeminiTTS` | Gemini speech generation (SSE) | PCM deltas |

Wit.ai is an audio-input speech recognition/NLU service rather than a
text-to-speech provider, so it belongs on the capture/upload side and is not
presented as a TTS backend.

MIP package: `github:PyDevices/micropython-hardware/packages/tts.json`

```python
from tts import KokoroTTS, TTSClient

client = TTSClient(KokoroTTS(base_url="http://192.168.1.10:8880/v1"))
client.speak("Hello from MicroPython.", board_config.audio_out)
```

## Local Kokoro TTS

[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) runs on a host PC; the
MCU only streams PCM over HTTP. Any OpenAI-shaped `/v1/audio/speech` server that
returns **raw 24 kHz mono PCM** works with `KokoroTTS`. For play-while-generating
on MicroPython, the server must stream the body **without**
`Transfer-Encoding: chunked` for HTTP/1.0 clients.

### Why `--http h11` matters

MicroPython’s `requests` library issues **HTTP/1.0** and raises if the response
advertises chunked transfer. Uvicorn’s default httptools backend always adds
chunked encoding when `Content-Length` is unknown. Run:

```bash
uvicorn server:app --host 0.0.0.0 --port 8880 --http h11
```

With h11, HTTP/1.0 peers get body-until-`Connection: close`, so
`TTSClient.speak` can write PCM to `audio_out` as chunks arrive.

### Host server (CPU)

A minimal FastAPI reference server lives in the PyDevices workspace as
`kokoro-tts/` (sibling of `micropython-hardware` / `pydisplay`). Summary:

```bash
cd kokoro-tts
uv venv .venv
uv pip install --python .venv/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python \
  https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8880 --http h11
```

- Health: `GET http://HOST:8880/health` → should include `"pcm_streaming": true`
- Speech: `POST http://HOST:8880/v1/audio/speech` with
  `{"model":"kokoro","input":"…","voice":"af_heart","response_format":"pcm"}`
- Multi-sentence text (`.?!` / newlines) yields earlier first audio than one
  long undivided clause

Third-party Kokoro OpenAI wrappers may work for desktop clients but often buffer
fully or use chunked encoding; prefer a server verified with HTTP/1.0 as above.

### Board UI examples (ESP32-P4)

| Example | Setup script | Secrets |
|---------|--------------|---------|
| [tts_kokoro.py](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tts_kokoro.py) | `setup_tts_kokoro.py` | `KOKORO_BASE_URL` |
| [tts_gemini.py](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tts_gemini.py) | `setup_tts_gemini.py` | `GEMINI_API_KEY` |
| [tts_orpheus.py](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tts_orpheus.py) | `setup_tts_orpheus.py` | `ORPHEUS_BASE_URL` |

Board package:
[`board_configs/fbdisplay/esp32-p4-wifi6-touch-lcd-4b/`](../board_configs/fbdisplay/esp32-p4-wifi6-touch-lcd-4b/)

**1. Firmware** with frozen lvgl, display_driver, MIPI-DSI / FBDisplay stack, and
`requests` (TLS required for Gemini).

**2. Put helpers on the board** (serial / mpftp — not installed by the setup
script):

```python
# /secrets.py — include the fields your UI needs
WIFI_SSID = "your-ssid"
WIFI_PASSWORD = "your-password"
KOKORO_BASE_URL = "http://192.168.1.10:8880/v1"
GEMINI_API_KEY = "…"
ORPHEUS_BASE_URL = "http://192.168.1.10:5005/v1"
```

Also provide `/wifi.py` with `connect_from_secrets()` (pydisplay utils or your
own).

**3. Reachability (local servers)** — From the board, `GET http://HOST:8880/health`
(Kokoro) or the Orpheus bridge URL must succeed. On WSL2, allow the TCP port on
the Windows firewall and/or port-proxy; use the Windows **LAN** address when the
ESP32 cannot route to a WSL-only veth.

**4. MIP install** (WiFi connected), e.g. Kokoro:

```python
import mip
mip.install(
    "github:PyDevices/micropython-hardware/board_configs/fbdisplay/"
    "esp32-p4-wifi6-touch-lcd-4b/setup_tts_kokoro.py",
    target="/",
)
import setup_tts_kokoro
```

Swap `setup_tts_gemini` / `setup_tts_orpheus` for the other UIs. Each writes
`/main.py` (`wifi` → `import tts_*`).

**5. Launch** — Soft-reset skips `main.py` on MicroPython. Soft-reboot
(`Ctrl-D`) or hard-reset, or `import tts_kokoro` (etc.) from the REPL after WiFi.

Desktop / unix MicroPython can use the same examples with localhost URLs and
`board_config.audio_out` (SDL).

## Orpheus (LM Studio)

Quantized model (CPU/GPU friendly):
[isaiahbjork/orpheus-3b-0.1-ft-Q4_K_M-GGUF](https://huggingface.co/isaiahbjork/orpheus-3b-0.1-ft-Q4_K_M-GGUF)

1. Install [LM Studio](https://lmstudio.ai/) and download that GGUF.
2. Load the model and start LM Studio’s local server (often `http://127.0.0.1:1234`).
3. Run an OpenAI `/v1/audio/speech` bridge that talks to LM Studio, e.g.
   [Orpheus-FastAPI-LMStudio](https://github.com/TheLocalLab/Orpheus-FastAPI-LMStudio)
   on `:5005`, or [orpheus-tts-local](https://github.com/isaiahbjork/orpheus-tts-local)
   for CLI/WAV workflows.
4. Point the MCU at the **bridge** (not LM Studio’s chat port alone):

   ```python
   from tts import OrpheusTTS, TTSClient
   client = TTSClient(OrpheusTTS(base_url="http://192.168.1.10:5005/v1"))
   ```

Emotion tags (`<laugh>`, `<sigh>`, `<chuckle>`, …) belong in the spoken text
(or the Style field in `tts_orpheus`, which prepends them). Voices:
`tara`, `leah`, `jess`, `leo`, `dan`, `mia`, `zac`, `zoe`.

`OrpheusTTS` expects a **WAV** body from the bridge; `TTSClient` strips the
header to raw 24 kHz PCM for `audio_out`.

## Gemini TTS

Cloud streaming via `GeminiTTS` + `secrets.GEMINI_API_KEY`. LVGL UI:
[`tts_gemini.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tts_gemini.py).
Style / pace / accent are prompt-driven (`instructions`). Quota errors may
include a retry delay; the UI counts down before re-enabling Speak.

## ESP32-P4 status

The Waveshare ESP32-P4 configuration uses one half-duplex session for its I2S
peripheral and ES8311. Playback exposes hardware DAC volume/mute and controls
the speaker amplifier; capture exposes hardware ADC gain. Register, stream,
session, and GPIO behavior is covered by host simulations. On-device TTS UIs
(`tts_kokoro` + local Kokoro streaming; Gemini / Orpheus via the same
`audio_out` path) have been exercised over WiFi.

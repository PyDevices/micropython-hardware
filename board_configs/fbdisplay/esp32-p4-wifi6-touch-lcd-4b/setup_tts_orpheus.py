# On-device mip setup: Waveshare ESP32-P4-WIFI6-Touch-LCD-4B → tts_orpheus
#
# Host: load Orpheus GGUF in LM Studio, run Orpheus FastAPI bridge on :5005.
#   https://huggingface.co/isaiahbjork/orpheus-3b-0.1-ft-Q4_K_M-GGUF
#   https://pydevices.github.io/micropython-hardware/audio.html#orpheus-lm-studio
#
# Prerequisites (USB/serial put — not installed here):
#   /wifi.py
#   /secrets.py   # WIFI_SSID, WIFI_PASSWORD, ORPHEUS_BASE_URL
#                 # e.g. ORPHEUS_BASE_URL = "http://192.168.1.10:5005/v1"
#
# Firmware must include frozen lvgl, display_driver, mipidsi, requests.
#
# Usage (WiFi up):
#   import mip; mip.install(
#       "github:PyDevices/micropython-hardware/board_configs/fbdisplay/"
#       "esp32-p4-wifi6-touch-lcd-4b/setup_tts_orpheus.py",
#       target="/",
#   )
#   import setup_tts_orpheus

import mip

INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
BOARD_PKG = (
    "github:PyDevices/micropython-hardware/board_configs/fbdisplay/"
    "esp32-p4-wifi6-touch-lcd-4b/package.json"
)

MAIN_PY = """\
import wifi

assert wifi.connect_from_secrets(), "wifi failed"
print("wifi ok;", wifi.radio.ipv4_address)
import tts_orpheus  # UI + runtime.run_forever()
"""


def main():
    import wifi

    assert wifi.connect_from_secrets(), "wifi failed"
    print("wifi", wifi.radio.ipv4_address)

    print("mip board package…")
    mip.install(BOARD_PKG, index=INDEX, target="/lib")

    print("mip tts…")
    mip.install(
        "github:PyDevices/micropython-hardware/packages/tts.json",
        target="/lib",
    )

    print("mip tts_orpheus…")
    mip.install(
        "github:PyDevices/pydisplay/src/examples/tts_orpheus.py",
        target="/lib",
    )

    with open("/main.py", "w") as f:
        f.write(MAIN_PY)
    print("wrote /main.py")
    print("done — soft-reboot (Ctrl-D) or hard-reset to launch tts_orpheus")


main()

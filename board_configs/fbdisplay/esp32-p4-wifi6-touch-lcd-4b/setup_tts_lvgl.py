# On-device mip setup: Waveshare ESP32-P4-WIFI6-Touch-LCD-4B → tts_lvgl
#
# Prerequisites (USB/serial put — not installed here):
#   /wifi.py
#   /secrets.py   # WIFI_SSID, WIFI_PASSWORD, GEMINI_API_KEY
#
# Firmware must include frozen lvgl, display_driver, mipidsi, requests.
#
# Usage (WiFi up via wifi.py + secrets):
#   import mip; mip.install(
#       "github:PyDevices/micropython-hardware/board_configs/fbdisplay/"
#       "esp32-p4-wifi6-touch-lcd-4b/setup_tts_lvgl.py",
#       target="/",
#   )
#   import setup_tts_lvgl
# Or paste/exec this file over the REPL after connecting WiFi.

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
import tts_lvgl  # UI + runtime.run_forever()
"""


def main():
    import wifi

    assert wifi.connect_from_secrets(), "wifi failed"
    print("wifi", wifi.radio.ipv4_address)

    # index= so bare deps like "displaysys" resolve from PyDevices MIP
    # (not micropython.org). displaysys → eventsys → multimer via package deps.
    print("mip board package…")
    mip.install(BOARD_PKG, index=INDEX, target="/lib")

    print("mip tts…")
    mip.install(
        "github:PyDevices/micropython-hardware/packages/tts.json",
        target="/lib",
    )

    print("mip tts_lvgl…")
    mip.install(
        "github:PyDevices/pydisplay/src/examples/tts_lvgl.py",
        target="/lib",
    )

    with open("/main.py", "w") as f:
        f.write(MAIN_PY)
    print("wrote /main.py")
    print("done — soft-reboot (Ctrl-D) or hard-reset to launch tts_lvgl")


main()

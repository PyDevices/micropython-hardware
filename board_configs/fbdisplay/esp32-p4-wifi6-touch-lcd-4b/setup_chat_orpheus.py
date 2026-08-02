# On-device mip setup: Waveshare ESP32-P4 → chat_orpheus (Gemma chat + Orpheus TTS)
#
# Secrets:
#   WIFI_*, LM_STUDIO_BASE_URL, CHAT_MODEL, ORPHEUS_BASE_URL
#   CHAT_MODEL default on-device: google/gemma-4-e4b
#
# Usage (WiFi up):
#   import mip; mip.install(
#       "github:PyDevices/micropython-hardware/board_configs/fbdisplay/"
#       "esp32-p4-wifi6-touch-lcd-4b/setup_chat_orpheus.py",
#       target="/",
#   )
#   import setup_chat_orpheus

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
import chat_orpheus  # UI + runtime.run_forever()
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

    print("mip chat_orpheus…")
    mip.install(
        "github:PyDevices/pydisplay/src/examples/chat_orpheus.py",
        target="/lib",
    )

    with open("/main.py", "w") as f:
        f.write(MAIN_PY)
    print("wrote /main.py")
    print("done — soft-reboot (Ctrl-D) or hard-reset to launch chat_orpheus")


main()

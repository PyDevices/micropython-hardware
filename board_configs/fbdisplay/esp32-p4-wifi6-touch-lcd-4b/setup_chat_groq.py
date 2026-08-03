# On-device mip setup: Waveshare ESP32-P4 -> Groq chat, STT, and TTS.

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
import chat_groq
"""


def main():
    import wifi

    assert wifi.connect_from_secrets(), "wifi failed"
    print("wifi", wifi.radio.ipv4_address)

    mip.install(BOARD_PKG, index=INDEX, target="/lib")
    mip.install(
        "github:PyDevices/micropython-hardware/packages/tts.json", target="/lib"
    )
    mip.install(
        "github:PyDevices/micropython-hardware/packages/stt.json", target="/lib"
    )
    mip.install(
        "github:PyDevices/pydisplay/src/examples/chat_groq.py", target="/lib"
    )

    with open("/main.py", "w") as main_py:
        main_py.write(MAIN_PY)
    print("done - hard-reset to launch chat_groq")


main()

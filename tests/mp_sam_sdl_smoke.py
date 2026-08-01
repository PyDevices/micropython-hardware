"""MicroPython Unix end-to-end SAM to SDL smoke test."""

import sys

sys.path.append("/tmp")
sys.path.append("../../micropython-hardware/drivers/audio")
sys.path.append("../../micropython-hardware/examples/audio")

from sam_sdl_app import main


main()
print("SAM to SDL MicroPython smoke: PASS")

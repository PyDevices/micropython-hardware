# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Put pydevices packages on ``sys.path`` for unit tests.

Import this before ``audiodev`` / ``usdl2`` / ``displaydev`` / ``multimer`` /
``mip`` so the in-repo trees are found without a separate install.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

for _rel in (
    "lib",
    "utils",
    "drivers",
    "drivers/codec",
    "drivers/io_expander",
):
    _path = str(ROOT / _rel)
    if _path not in sys.path:
        sys.path.insert(0, _path)

PATH_ENTRIES = [
    str(ROOT / "lib"),
    str(ROOT / "utils"),
    str(ROOT / "drivers"),
    str(ROOT / "drivers" / "display"),
]

DISPLAYDEV_DIR = str(ROOT / "lib" / "displaydev")
MULTIMER_DIR = str(ROOT / "lib" / "multimer")
APPDEV_DIR = str(ROOT / "lib" / "appdev")
EVENTS_PY = str(ROOT / "lib" / "events.py")
KEYS_PY = str(ROOT / "lib" / "keys.py")

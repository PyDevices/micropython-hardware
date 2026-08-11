# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Put micropython-hardware packages on ``sys.path`` for unit tests.

Import this before ``audiodev`` / ``usdl2`` / ``displaydev`` / ``multimer``
so the in-repo trees are found without a separate install.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

for _rel in (
    "lib",
    "drivers",
    "drivers/audio",
    "drivers/display",
    "drivers/codec",
    "drivers/io_expander",
):
    _path = str(ROOT / _rel)
    if _path not in sys.path:
        sys.path.insert(0, _path)

DISPLAYDEV_DIR = str(ROOT / "drivers" / "display" / "displaydev")
MULTIMER_DIR = str(ROOT / "lib" / "multimer")
EVENTS_PY = str(ROOT / "lib" / "events.py")
KEYS_PY = str(ROOT / "lib" / "keys.py")

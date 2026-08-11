# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Put micropython-hardware drivers on ``sys.path`` for unit tests.

Import this before ``audiodev`` / ``usdl2`` so the in-repo
pure-Python ``drivers/usdl2.py`` is found without a separate install.
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

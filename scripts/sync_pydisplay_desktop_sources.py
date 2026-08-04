#!/usr/bin/env python3
"""Generate pydisplay-desktop staging package from canonical MIP sources.

The canonical implementation lives in:
- board_configs/desktop/board_config.py
- board_configs/desktop/board_devices.py
- drivers/boarddev.py
- drivers/audio/audiodev.py
- drivers/audio/sdl2audio.py

This script writes a throwaway staging tree so the pip package and MIP package
stay behaviorally identical.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


MAPPINGS = (
    ("board_configs/desktop/board_config.py", "src/board_config.py"),
    ("board_configs/desktop/board_devices.py", "src/board_devices.py"),
    ("drivers/boarddev.py", "src/boarddev.py"),
    ("drivers/audio/audiodev.py", "src/audiodev.py"),
    ("drivers/audio/sdl2audio.py", "src/sdl2audio.py"),
)


METADATA_FILES = (
    ("pyproject.toml", "pyproject.toml"),
    ("docs/pydisplay-desktop.md", "README.md"),
)


def sync(root: Path, stage_dir: Path, check: bool) -> int:
    changed = []
    for src_rel, dst_rel in (*MAPPINGS, *METADATA_FILES):
        src = root / src_rel
        dst = stage_dir / dst_rel
        if not src.exists():
            print(f"Missing source file: {src}", file=sys.stderr)
            return 2
        if not dst.exists():
            changed.append((src_rel, str(dst.relative_to(stage_dir))))
            if not check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
            continue

        src_bytes = src.read_bytes()
        dst_bytes = dst.read_bytes()
        if src_bytes != dst_bytes:
            changed.append((src_rel, str(dst.relative_to(stage_dir))))
            if not check:
                shutil.copyfile(src, dst)

    if check:
        if changed:
            print(f"pydisplay-desktop staging files are out of sync in {stage_dir}:")
            for src_rel, dst_rel in changed:
                print(f"  {dst_rel} <- {src_rel}")
            return 1
        print(f"pydisplay-desktop staging files are in sync in {stage_dir}.")
        return 0

    if changed:
        print(f"Synced pydisplay-desktop staging files in {stage_dir}:")
        for src_rel, dst_rel in changed:
            print(f"  {dst_rel} <- {src_rel}")
    else:
        print(f"pydisplay-desktop staging files already in sync in {stage_dir}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if staging files differ from canonical sources.",
    )
    parser.add_argument(
        "--stage-dir",
        default=".pydisplay-desktop-build",
        help="Throwaway staging directory to generate/update.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    stage_dir = (root / args.stage_dir).resolve()
    stage_dir.mkdir(parents=True, exist_ok=True)
    return sync(root, stage_dir=stage_dir, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())

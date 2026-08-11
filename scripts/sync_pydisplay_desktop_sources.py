#!/usr/bin/env python3
"""Generate pydisplay-desktop staging package from canonical MIP sources.

The canonical implementation lives in:
- board_configs/desktop/board_config.py
- board_configs/desktop/board_devices.py
- drivers/boarddev.py
- drivers/audio/audiodev/ (package)
- drivers/usdl2.py

This script writes a throwaway staging tree so the pip package and MIP package
stay behaviorally identical.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


FILE_MAPPINGS = (
    ("board_configs/desktop/board_config.py", "src/board_config.py"),
    ("board_configs/desktop/board_devices.py", "src/board_devices.py"),
    ("drivers/boarddev.py", "src/boarddev.py"),
    ("drivers/usdl2.py", "src/usdl2.py"),
)

DIR_MAPPINGS = (("drivers/audio/audiodev", "src/audiodev"),)

METADATA_FILES = (
    ("pyproject.toml", "pyproject.toml"),
    ("docs/pydisplay-desktop.md", "README.md"),
)


def _copy_dir(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def _dir_matches(src: Path, dst: Path) -> bool:
    if not dst.exists():
        return False
    src_files = {p.relative_to(src): p.read_bytes() for p in src.rglob("*") if p.is_file()}
    dst_files = {p.relative_to(dst): p.read_bytes() for p in dst.rglob("*") if p.is_file()}
    return src_files == dst_files


def sync(root: Path, stage_dir: Path, check: bool) -> int:
    changed = []
    for src_rel, dst_rel in FILE_MAPPINGS:
        src = root / src_rel
        dst = stage_dir / dst_rel
        if not src.exists():
            print(f"Missing source file: {src}", file=sys.stderr)
            return 2
        if not dst.exists() or src.read_bytes() != dst.read_bytes():
            changed.append((src_rel, dst_rel))
            if not check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)

    for src_rel, dst_rel in DIR_MAPPINGS:
        src = root / src_rel
        dst = stage_dir / dst_rel
        if not src.exists():
            print(f"Missing source directory: {src}", file=sys.stderr)
            return 2
        if not _dir_matches(src, dst):
            changed.append((src_rel, dst_rel))
            if not check:
                _copy_dir(src, dst)

    for src_rel, dst_rel in METADATA_FILES:
        src = root / src_rel
        dst = stage_dir / dst_rel
        if not src.exists():
            print(f"Missing source file: {src}", file=sys.stderr)
            return 2
        if not dst.exists() or src.read_bytes() != dst.read_bytes():
            changed.append((src_rel, dst_rel))
            if not check:
                dst.parent.mkdir(parents=True, exist_ok=True)
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

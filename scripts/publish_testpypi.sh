#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if [[ -z "${TESTPYPI_API_TOKEN:-}" ]]; then
  echo "Error: TESTPYPI_API_TOKEN is not set." >&2
  echo "Set it and rerun: TESTPYPI_API_TOKEN=... ./scripts/publish_testpypi.sh" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
STAGE_DIR="${PYDISPLAY_DESKTOP_STAGE_DIR:-.pydisplay-desktop-build}"

rm -rf "$STAGE_DIR"
"$PYTHON_BIN" scripts/sync_pydisplay_desktop_sources.py --stage-dir "$STAGE_DIR"

rm -rf "$STAGE_DIR/build" "$STAGE_DIR/dist" "$STAGE_DIR/src/pydisplay_desktop.egg-info"
(
  cd "$STAGE_DIR"
  "$PYTHON_BIN" -m build
  "$PYTHON_BIN" -m twine check dist/*
  TWINE_USERNAME=__token__ TWINE_PASSWORD="$TESTPYPI_API_TOKEN" \
    "$PYTHON_BIN" -m twine upload --repository testpypi --verbose dist/*
)

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -z "${TESTPYPI_API_TOKEN:-}" ]]; then
  echo "Error: TESTPYPI_API_TOKEN is not set." >&2
  echo "Set it and rerun: TESTPYPI_API_TOKEN=... ./publish_testpypi.sh" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

rm -rf build dist src/pydisplay_desktop.egg-info
"$PYTHON_BIN" -m build
"$PYTHON_BIN" -m twine check dist/*

TWINE_USERNAME=__token__ TWINE_PASSWORD="$TESTPYPI_API_TOKEN" \
  "$PYTHON_BIN" -m twine upload --repository testpypi --verbose dist/*
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
STAGE_DIR="${PYDEVICES_DESKTOP_STAGE_DIR:-.pydevices-desktop-build}"

VERSION="${PYDEVICES_VERSION:-}"
if [[ -z "$VERSION" ]]; then
  VERSION="$(git describe --tags --exact-match 2>/dev/null || true)"
fi
VERSION="${VERSION#v}"
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
  echo "Error: set PYDEVICES_VERSION=X.Y.Z or run from an exact vX.Y.Z tag." >&2
  exit 1
fi

rm -rf "$STAGE_DIR"
"$PYTHON_BIN" scripts/sync_pydevices_desktop_sources.py --stage-dir "$STAGE_DIR"
sed -i -E "0,/^version = \"[^\"]+\"/s//version = \"$VERSION\"/" "$STAGE_DIR/pyproject.toml"
grep -q "^version = \"$VERSION\"$" "$STAGE_DIR/pyproject.toml" || {
  echo "Error: failed to set pydevices-desktop version $VERSION" >&2
  exit 1
}

rm -rf "$STAGE_DIR/build" "$STAGE_DIR/dist" "$STAGE_DIR/src/pydevices_desktop.egg-info"
(
  cd "$STAGE_DIR"
  "$PYTHON_BIN" -m build
  "$PYTHON_BIN" -m twine check dist/*
  TWINE_USERNAME=__token__ TWINE_PASSWORD="$TESTPYPI_API_TOKEN" \
    "$PYTHON_BIN" -m twine upload --repository testpypi --verbose dist/*
)

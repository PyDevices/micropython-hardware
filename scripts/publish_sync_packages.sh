#!/usr/bin/env bash
# Publish the canonical PyDevices Python packages from pydevices.
#
# TestPyPI distributions are named pydevices-<mip-name>. MIP package names and
# Python import names remain unprefixed (displaydev, audiodev, eventsys, ...).

set -euo pipefail

SKIP_PYPI=0
DO_PUSH=0
COMMIT_MESSAGE=""
CLI_VERSION=""

usage() {
    cat <<'EOF'
Usage: ./scripts/publish_sync_packages.sh [OPTION]

Sync canonical packages into a PyDevices/micropython-lib checkout, optionally
build/upload TestPyPI distributions, and optionally commit/push the PyDevices
branch.

Options:
  --skip-pypi           Sync MIP manifests only; do not upload TestPyPI.
  --version X.Y.Z       Release version (overrides tag / PYDEVICES_VERSION).
  --commit-message MSG  Commit micropython-lib changes.
  --push                Push micropython-lib after committing.
  --help, -h            Show this message.

Environment:
  MICROPYTHON_LIB_DIR   micropython-lib checkout (default: sibling checkout)
  PYDEVICES_VERSION    Release version when no --version is supplied
  TESTPYPI_API_TOKEN   TestPyPI token (required by non-interactive CI uploads)
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-pypi) SKIP_PYPI=1; shift ;;
        --version) CLI_VERSION=$2; shift 2 ;;
        --commit-message) COMMIT_MESSAGE=$2; shift 2 ;;
        --push) DO_PUSH=1; shift ;;
        --help | -h) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST_REPO="${MICROPYTHON_LIB_DIR:-$SOURCE_REPO/../micropython-lib}"
DEST_REPO="$(cd "$DEST_REPO" && pwd)"
DEST_DIR="$DEST_REPO/micropython/pydevices"
LEGACY_DEST_DIR="$DEST_REPO/micropython/pydisplay"
PYPI_DIR="$SOURCE_REPO/wheels"
export MICROPYTHON_LIB_DIR="$DEST_REPO"

normalize_version() {
    local version="${1#v}"
    version="$(echo "$version" | tr -d '[:space:]')"
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
        echo "Invalid semver: $1 (expected X.Y.Z)" >&2
        return 1
    fi
    echo "$version"
}

resolve_version() {
    if [[ -n "$CLI_VERSION" ]]; then normalize_version "$CLI_VERSION"; return; fi
    if [[ -n "${PYDEVICES_VERSION:-}" ]]; then normalize_version "$PYDEVICES_VERSION"; return; fi
    local tag
    tag="$(git -C "$SOURCE_REPO" describe --tags --exact-match 2>/dev/null || true)"
    if [[ -n "$tag" ]]; then normalize_version "$tag"; return; fi
    echo "No release version: pass --version, set PYDEVICES_VERSION, or tag HEAD vX.Y.Z." >&2
    return 1
}

VERSION="$(resolve_version)"
AUTHOR="Brad Barnett <contact@pydevices.com>"
LICENSE="MIT"

RSYNC_EXCLUDES=(
    --exclude '__pycache__/' --exclude '*.pyc' --exclude '*.pyo'
    --exclude '.git/' --exclude '.mypy_cache/' --exclude '.ruff_cache/'
)

pypi_name() { echo "pydevices-$1"; }

summary() {
    case "$1" in
        displaydev) echo "Cross-platform display drivers for MicroPython, CircuitPython, and CPython" ;;
        audiodev) echo "Cross-platform PCM audio interfaces for MicroPython, CircuitPython, and CPython" ;;
        eventsys) echo "Optional application event traffic controller and input adapters" ;;
        events) echo "SDL2/PyGame-style event types and namedtuple event classes" ;;
        keys) echo "SDL-style key codes, modifier masks, and chord matching" ;;
        multimer) echo "Cross-platform machine.Timer-style and asyncio timers" ;;
        *) echo "PyDevices $1" ;;
    esac
}

requires() {
    case "$1" in
        displaydev) printf '%s\n' 'require("events")' 'require("keys")' ;;
        eventsys) printf '%s\n' 'require("events")' 'require("keys")' 'require("multimer")' ;;
    esac
}

source_dir() {
    case "$1" in
        displaydev) echo "$SOURCE_REPO/drivers/display/displaydev" ;;
        audiodev) echo "$SOURCE_REPO/drivers/audio/audiodev" ;;
        eventsys | multimer) echo "$SOURCE_REPO/lib/$1" ;;
    esac
}

readme_path() {
    case "$1" in
        displaydev) echo "$SOURCE_REPO/drivers/display/displaydev/README.md" ;;
        audiodev) echo "$SOURCE_REPO/drivers/audio/README.md" ;;
        eventsys | multimer) echo "$SOURCE_REPO/lib/$1/README.md" ;;
    esac
}

copy_tree() {
    local source=$1 destination=$2
    mkdir -p "$destination"
    rsync -a --delete "${RSYNC_EXCLUDES[@]}" "$source/" "$destination/"
}

write_manifest() {
    local package=$1 manifest=$2 kind=$3
    local extra payload
    extra="$(requires "$package")"
    if [[ "$kind" == "module" ]]; then
        payload="module(\"$package.py\")"
    else
        payload="package(\"$package\")"
    fi
    cat > "$manifest" <<EOF
metadata(
    description="$(summary "$package")",
    version="$VERSION",
    author="$AUTHOR",
    license="$LICENSE",
    pypi_publish="$(pypi_name "$package")",
)
${extra}
${payload}
EOF
}

build_and_upload() {
    local package=$1 manifest=$2
    [[ "$SKIP_PYPI" -eq 0 ]] || return 0
    local out="$PYPI_DIR/$package"
    rm -rf "$out"
    "$SOURCE_REPO/scripts/publish_make_pyproject.py" --output "$out" "$manifest"
    (cd "$out" && hatch build)
    if [[ -n "${TESTPYPI_API_TOKEN:-}" ]]; then
        TWINE_USERNAME=__token__ TWINE_PASSWORD="$TESTPYPI_API_TOKEN" \
            twine upload --repository testpypi --skip-existing --verbose "$out"/dist/*
    else
        twine upload --repository testpypi --skip-existing --verbose "$out"/dist/*
    fi
}

publish_package() {
    local package=$1 source readme package_dir
    source="$(source_dir "$package")"
    readme="$(readme_path "$package")"
    package_dir="$DEST_DIR/$package"
    echo "Processing $package -> $(pypi_name "$package")"
    copy_tree "$source" "$package_dir/$package"
    write_manifest "$package" "$package_dir/manifest.py" package
    cp "$readme" "$package_dir/README.md"
}

publish_module() {
    local package=$1 package_dir="$DEST_DIR/$1"
    echo "Processing $package -> $(pypi_name "$package")"
    mkdir -p "$package_dir"
    cp "$SOURCE_REPO/lib/$package.py" "$package_dir/$package.py"
    write_manifest "$package" "$package_dir/manifest.py" module
    cat > "$package_dir/README.md" <<EOF
# $package

$(summary "$package").

Canonical source: [pydevices/lib/$package.py](https://github.com/PyDevices/pydevices/blob/main/lib/$package.py).
EOF
}

# The new source-of-truth collection replaces the stale legacy pydisplay package tree.
rm -rf "$DEST_DIR"
rm -rf "$LEGACY_DEST_DIR"
mkdir -p "$DEST_DIR"

for package in displaydev audiodev eventsys multimer; do publish_package "$package"; done
for package in events keys; do publish_module "$package"; done

# Build only after the complete collection exists, so require() can resolve
# sibling PyDevices packages while generating each TestPyPI project.
for package in displaydev audiodev eventsys multimer events keys; do
    build_and_upload "$package" "$DEST_DIR/$package/manifest.py"
done

find "$DEST_DIR" -type d -name __pycache__ -prune -exec rm -rf {} +

push_micropython_lib() {
    local branch attempt=1
    branch="$(git -C "$DEST_REPO" rev-parse --abbrev-ref HEAD)"
    while ! git -C "$DEST_REPO" push origin "HEAD:$branch"; do
        if (( attempt >= 8 )); then return 1; fi
        git -C "$DEST_REPO" fetch origin "$branch"
        git -C "$DEST_REPO" rebase "origin/$branch"
        attempt=$((attempt + 1))
    done
}

if [[ -n "$COMMIT_MESSAGE" ]]; then
    git -C "$DEST_REPO" add -A -- micropython/pydevices
    if [[ -d "$LEGACY_DEST_DIR" ]] || git -C "$DEST_REPO" ls-files -- micropython/pydisplay | grep -q .; then
        git -C "$DEST_REPO" add -A -- micropython/pydisplay
    fi
    if ! git -C "$DEST_REPO" diff --cached --quiet; then
        git -C "$DEST_REPO" commit -s -m "$COMMIT_MESSAGE"
        if [[ "$DO_PUSH" -eq 1 ]]; then push_micropython_lib; fi
    fi
elif [[ "$DO_PUSH" -eq 1 ]]; then
    echo "--push requires --commit-message" >&2
    exit 1
fi

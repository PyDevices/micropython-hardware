#!/usr/bin/env bash
# Create and push a release tag for this repo. Same interface in every PyDevices repo.
#
# Version is the optional VERSION argument, else auto-computed by
# next_release_version.sh (highest vX.Y.Z tag + 1 patch). Pushing the tag
# triggers this repo's publish workflow.
#
# Before tagging, pre-bumps every distribution published by this repo in the
# sibling pydevices-examples/requirements.txt and commits there when needed.
#
# Usage:
#   ./scripts/publish_release_tag.sh                # auto version; create tag
#   ./scripts/publish_release_tag.sh --push         # auto version; create + push
#   ./scripts/publish_release_tag.sh 0.0.5 --push   # explicit version; create + push
#   ./scripts/publish_release_tag.sh --dry-run      # preview only
#
# Preview the next version:  ./scripts/next_release_version.sh --verbose
#
# Override sibling checkout: PYDEVICES_EXAMPLES_ROOT=/path/to/pydevices-examples

set -euo pipefail

DO_PUSH=0
DRY_RUN=0
VERSION=""

usage() {
    cat <<'EOF'
Usage: ./scripts/publish_release_tag.sh [VERSION] [--push] [--dry-run]

Create an annotated git tag vVERSION on the current commit.

  VERSION     Optional semver X.Y.Z. When omitted, computed by
              scripts/next_release_version.sh (highest tag + 1 patch).
  --push      Push pydevices-examples floors (if committed), this branch, and the tag
  --dry-run   Print the version / floor bump; do not commit or tag

Before tagging, bumps the `pydevices-events`, `pydevices-keys`,
`pydevices-multimer`, `pydevices-displaydev`, `pydevices-audiodev`,
`pydevices-eventsys` and `pydevices-desktop` floors to VERSION in the sibling
pydevices-examples checkout (override with PYDEVICES_EXAMPLES_ROOT).

Examples:
  ./scripts/publish_release_tag.sh --push
  ./scripts/publish_release_tag.sh 0.0.5 --push
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --push)
            DO_PUSH=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --help | -h)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
        *)
            if [[ -n "$VERSION" ]]; then
                echo "Unexpected argument: $1" >&2
                usage >&2
                exit 1
            fi
            VERSION=$1
            shift
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"

AUTO=0
if [[ -z "$VERSION" ]]; then
    AUTO=1
    VERSION="$($SCRIPT_DIR/next_release_version.sh)"
fi

VERSION="${VERSION#v}"
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: expected semver X.Y.Z, got: $VERSION" >&2
    exit 1
fi

TAG="v$VERSION"

resolve_examples_root() {
    if [[ -n "${PYDEVICES_EXAMPLES_ROOT:-}" ]]; then
        printf '%s\n' "$(cd "$PYDEVICES_EXAMPLES_ROOT" && pwd)"
        return
    fi
    local sibling="$SOURCE_REPO/../pydevices-examples"
    if [[ -d "$sibling/scripts" && -f "$sibling/requirements.txt" ]]; then
        printf '%s\n' "$(cd "$sibling" && pwd)"
        return
    fi
    local home_sibling="${HOME}/gh/pydevices/pydevices-examples"
    if [[ -d "$home_sibling/scripts" && -f "$home_sibling/requirements.txt" ]]; then
        printf '%s\n' "$(cd "$home_sibling" && pwd)"
        return
    fi
    echo "Error: pydevices-examples checkout not found (set PYDEVICES_EXAMPLES_ROOT)." >&2
    return 1
}

cd "$SOURCE_REPO"

# Dirty tree only matters for real tag/commit; allow --dry-run on WIP branches.
if [[ "$DRY_RUN" -eq 0 ]]; then
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "Error: working tree has uncommitted changes; commit or stash before tagging." >&2
        exit 1
    fi
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Error: tag $TAG already exists ($(git rev-parse --short "$TAG^{commit}"))" >&2
    exit 1
fi

if [[ "$AUTO" -eq 1 ]]; then
    "$SCRIPT_DIR/next_release_version.sh" --verbose
else
    echo "Version: ${VERSION} (explicit)"
fi

PYDEVICES_EXAMPLES_ROOT="$(resolve_examples_root)"
echo "Pre-bump pydevices TestPyPI distributions to >=${VERSION} in ${PYDEVICES_EXAMPLES_ROOT}/requirements.txt"

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Dry run — would bump pydevices-examples floors, commit there if needed, then create tag $TAG here"
    exit 0
fi

if ! git -C "$PYDEVICES_EXAMPLES_ROOT" diff --quiet || ! git -C "$PYDEVICES_EXAMPLES_ROOT" diff --cached --quiet; then
    echo "Error: pydevices-examples working tree has uncommitted changes; commit or stash before tagging." >&2
    exit 1
fi

python3 "$PYDEVICES_EXAMPLES_ROOT/scripts/refresh-requirements.py" \
    --path "$PYDEVICES_EXAMPLES_ROOT/requirements.txt" \
    --set \
    "pydevices-events=${VERSION}" \
    "pydevices-keys=${VERSION}" \
    "pydevices-multimer=${VERSION}" \
    "pydevices-displaydev=${VERSION}" \
    "pydevices-audiodev=${VERSION}" \
    "pydevices-eventsys=${VERSION}" \
    "pydevices-desktop=${VERSION}"

if ! git -C "$PYDEVICES_EXAMPLES_ROOT" diff --quiet -- requirements.txt; then
    git -C "$PYDEVICES_EXAMPLES_ROOT" add requirements.txt
    git -C "$PYDEVICES_EXAMPLES_ROOT" commit -m "$(cat <<EOF
Bump pydevices TestPyPI floors for v${VERSION}.

EOF
)"
    echo "Committed pydevices-examples requirements.txt floors for pydevices $VERSION"
    if [[ "$DO_PUSH" -eq 1 ]]; then
        git -C "$PYDEVICES_EXAMPLES_ROOT" push origin HEAD
        echo "Pushed pydevices-examples HEAD"
    fi
else
    echo "pydevices floors already at $VERSION; no pydevices-examples floor commit"
fi

git tag -a "$TAG" -m "Release $VERSION"
echo "Created annotated tag $TAG on $(git rev-parse --short HEAD)"

if [[ "$DO_PUSH" -eq 1 ]]; then
    git push origin HEAD
    git push origin "$TAG"
    echo "Pushed HEAD and $TAG — this repo's publish workflow should start shortly."
else
    echo "Push to publish: git push origin HEAD && git push origin $TAG"
fi

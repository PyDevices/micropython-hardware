# pydisplay-desktop

Desktop bundle for non-MCU hosts using PyDevices display/runtime modules.

Installed modules:
- board_config
- boarddev
- audiodev
- sdl2audio

This package is intended to provide a single pip-installable desktop config
bundle while core runtime libraries continue to come from PyDevices packages.

`board_config.py` ownership for packaged desktop installs lives here
(`pydisplay-desktop`), analogous to the MIP desktop bundle in
`board_configs/desktop`.

## Install (TestPyPI)

Install and verification flows are centralized here:
[../../docs/install-workflows.md](../../docs/install-workflows.md)

Use the sections:
- "pydisplay-desktop via pip"
- "Verify with .venv"
- "Verify without .venv (python.exe / pip.exe)"

`board_config` uses lazy initialization. Display/audio setup runs when runtime
objects are first accessed, not at import time.

## Publish to TestPyPI

```bash
cd python/pydisplay-desktop
TESTPYPI_API_TOKEN=... ./publish_testpypi.sh
```

## Tag-based Release (repo-standard)

Use the repository-level tag scripts, consistent with other PyDevices repos:

1. Preview next version:

	./scripts/next_release_version.sh --verbose

2. Create and push release tag:

	./scripts/publish_release_tag.sh --push

Pushing a `vX.Y.Z` tag triggers `.github/workflows/publish-pydisplay-desktop.yml`,
which sets the package version from the tag and uploads to TestPyPI.

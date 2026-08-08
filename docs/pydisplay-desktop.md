# pydisplay-desktop

Desktop bundle for non-MCU hosts using PyDevices display/runtime modules.

Installed modules:
- board_config
- board_devices
- boarddev
- audiodev
- sdl2audio
- androidaudio_session
- usdl2
- pygameaudio
- webaudio

Source of truth:
- Runtime modules are generated from canonical sources in this repo
  (`board_configs/desktop/` and `drivers/`).
- Use `scripts/sync_pydisplay_desktop_sources.py` to stage package files for
  build/publish and avoid drift between MIP and pip behavior.

This package is intended to provide a single pip-installable desktop config
bundle while core runtime libraries continue to come from PyDevices packages.

`board_config.py` ownership for packaged desktop installs lives here
(`pydisplay-desktop`), analogous to the MIP desktop bundle in
`board_configs/desktop`.

## Install (TestPyPI)

Install and verification flows are centralized here:
[install-workflows.md](install-workflows.md)

Use the sections:
- "pydisplay-desktop via pip"
- "Verify with .venv"
- "Verify without .venv (python.exe / pip.exe)"

`board_config` constructs `display_drv` and `runtime` at import time (MCU-shaped
eager wiring via `displaysys.AutoDisplay`). Lazy roles such as `audio_out` /
`audio_in` still come from `board_devices` and allocate on first access.
Terminal-only apps can `import board_devices` without opening a window.

## Publish to TestPyPI

```bash
TESTPYPI_API_TOKEN=... ./scripts/publish_testpypi.sh
```

## Tag-based Release (repo-standard)

Use the repository-level tag scripts, consistent with other PyDevices repos:

1. Preview next version:

	./scripts/next_release_version.sh --verbose

2. Create and push release tag:

	./scripts/publish_release_tag.sh --push

Pushing a `vX.Y.Z` tag triggers `.github/workflows/publish-pydisplay-desktop.yml`,
which sets the package version from the tag and uploads to TestPyPI.

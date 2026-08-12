# pydevices-desktop

Desktop board and host-adapter bundle for non-MCU PyDevices applications.

Installed modules:
- board_config
- board_peripherals
- boarddev
- micropython (CPython compatibility shim)
- usdl2
- uwin32 (Windows CPython)

It depends on `pydevices-displaydev` and `pydevices-audiodev`. The optional
`pydevices-eventsys` application traffic controller is installed separately by
applications that want it; LVGL does not require it.

Source of truth:
- Runtime modules are generated from canonical sources in this repo
  (`board_configs/desktop/` and `drivers/`).
- Use `scripts/sync_pydevices_desktop_sources.py` to stage package files for
  build/publish and avoid drift between MIP and pip behavior.

This package is intended to provide a single pip-installable desktop config
bundle while core runtime libraries continue to come from PyDevices packages.

`board_config.py` ownership for packaged desktop installs lives here
(`pydevices-desktop`), analogous to the MIP desktop bundle in
`board_configs/desktop`.

## Install (TestPyPI)

Install and verification flows are centralized here:
[install-workflows.md](install-workflows.md)

Use the sections:
- "pydevices-desktop via pip"
- "Verify with .venv"
- "Verify without .venv (python.exe / pip.exe)"

`board_config` constructs `display_drv` and exports neutral host/input callables
via `displaydev.auto.AutoDisplay`; it does not create an event runtime. Lazy roles such as `audio_out` /
`audio_in` still come from `board_peripherals` and allocate on first access.
Terminal-only apps can `import board_peripherals` without opening a window.

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

Pushing a `vX.Y.Z` tag triggers `.github/workflows/publish-pydevices.yml`,
which sets the package version from the tag and uploads to TestPyPI.

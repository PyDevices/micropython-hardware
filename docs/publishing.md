# Publishing PyDevices

One published GitHub Release named `vX.Y.Z` publishes every artifact generated
from this repository with version `X.Y.Z`. `VERSION` must already contain that
same version.

## Generated products

Every non-debris top-level module or package under `lib/` is discovered as a
leaf. Today those leaves are `audiodev`, `displaydev`, `events`, `eventsys`,
`keys`, and `multimer`. Adding another component under `lib/` automatically
adds its unprefixed MIP package and its `pydevices-<name>` TestPyPI
distribution; there is no include list.

The dependency-only `pydevices` meta-package installs every discovered leaf,
including `eventsys`. The `pydevices-desktop` meta-package depends on
`pydevices` and also installs the desktop board files plus every runtime module
discovered under `utils/`. Utilities do not have separate distributions.

All internal TestPyPI requirements use exact `==X.Y.Z` pins. MIP meta-package
requirements intentionally resolve `latest`, while each generated manifest
records `X.Y.Z` as its own version.

## Release pipeline

`.github/workflows/publish-release-packages.yml` is the only package release
coordinator. It calls versioned reusable workflows from `PyDevices/.github` at
`publishing-v1`, builds and validates all distributions, uploads the complete
set to TestPyPI with the existing API token, and sends one exact source
ref/version request to the serialized `PyDevices/mip` publication queue.

Manual retries require the exact existing `vX.Y.Z` tag. They never rebuild from
a moving branch.

## Board installers

Board `package.json` files are not published in the MIP index. Install them
directly from their raw GitHub directory. Hardware installers depend on
`pydevices` at `latest` and carry their board-specific Python drivers in their
own `urls`. Optional Python bus fallbacks are not pulled: firmware-provided
`i80bus`, `i2cbus`, `spibus`, and similar native modules take precedence.

The one desktop board installer depends on `pydevices-desktop` at `latest`.
Run `python scripts/validate_board_mip_installers.py` to validate every board
installer discovered under `board_configs/`.

## PyScript filesystem

`pydevices-desktop.toml` is a generated, committed filesystem mapping that
tracks `main`. It contains the complete Python payload of the desktop package
with explicit `/lib/...` destinations. CI fails if any discovered `lib/` or
`utils/` source, or one of the fixed desktop board files, is missing or stale.

## Required service configuration

- Repository secret `TESTPYPI_API_TOKEN`, currently owned by `bdbarnett` while
  the PyDevices TestPyPI organization request is pending.
- Repository secret `MICROPYTHON_LIB_DEPLOY_TOKEN` with access to dispatch the
  central MIP queue.
- Shared workflow ref `PyDevices/.github@publishing-v1`.

Published TestPyPI files and MIP releases are immutable in practice; publish a
new version to correct a release.

# Publishing

`pydevices` is the canonical source and release owner for the
portable PyDevices core. A single release tag publishes the core packages to
TestPyPI, syncs their unprefixed MIP packages into the PyDevices
`micropython-lib` fork, and rebuilds the PyDevices MIP index.

`pydevices-examples` is the examples and integration showcase. It consumes these
packages, but does not publish them.

## Package names

TestPyPI distributions use the `pydevices-` namespace. Python imports and MIP
package names stay short and unprefixed, matching normal MicroPython library
conventions.

| Canonical source | TestPyPI distribution | Python import / MIP name |
|---|---|---|
| `lib/displaydev/` | `pydevices-displaydev` | `displaydev` |
| `lib/audiodev/` | `pydevices-audiodev` | `audiodev` |
| `lib/eventsys/` | `pydevices-eventsys` | `eventsys` |
| `lib/multimer/` | `pydevices-multimer` | `multimer` |
| `lib/events.py` | `pydevices-events` | `events` |
| `lib/keys.py` | `pydevices-keys` | `keys` |
| `board_configs/desktop/` plus shared sources | `pydevices-desktop` | `board_config` and its dependencies |
| `release/pydevices/` | `pydevices` | portable MIP bundle `pydevices` |

`eventsys` is an optional application-level event traffic controller. Board
configs do not construct it. Non-LVGL applications may instantiate it (or
provide their own controller); the PyDevices LVGL display driver connects LVGL
to `displaydev` and `multimer` directly.

Companion repositories follow the same naming rule:

| Source repository | TestPyPI distribution | Python import / MIP name |
|---|---|---|
| `palettes` | `pydevices-palettes` | `palettes` |
| `pdwidgets` | `pydevices-pdwidgets` | `pdwidgets` |
| `pygraphics` | `pydevices-pygraphics` | `pygraphics` |
| `lvgl-python` | `pydevices-lvgl` | `lvgl` (pip only) |

## Install from TestPyPI

TestPyPI does not mirror dependencies from PyPI, so use both indexes:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  'pydevices[desktop]'
```

Install `pydevices-eventsys` only when the application wants that event
controller. See [install-workflows.md](install-workflows.md) for board-config
and verification examples.

## Install with MIP

In the MicroPython ecosystem, `https://micropython.org/pi/v2` serves as the default package index for `mip` (analogous to PyPI in CPython), fed by upstream `micropython/micropython-lib`.

For PyDevices, the [`PyDevices/mip`](https://github.com/PyDevices/mip) fork acts as the dedicated distribution and aggregation hub. PyDevices packages are synchronized into this fork, where CI builds and hosts the custom PyDevices MIP package index at:

```text
https://PyDevices.github.io/mip
```

This index hosts **both `.py` (source) and `.mpy` (precompiled bytecode)** artifacts:
- **`.mpy` (precompiled)**: Delivered by default for MicroPython targets for faster import speeds and reduced RAM consumption on microcontrollers.
- **`.py` (source)**: Available for development, inspection, or multi-runtime workflows when installing with `--no-mpy` / `mpy=False`.

Example install pointing to the PyDevices index:

```python
import mip

mip.install(
    "displaydev",
    index="https://PyDevices.github.io/mip",
)
```

Board package manifests declare their own driver and library dependencies within the index. They intentionally do not declare `eventsys`; the application owns that choice and its lifecycle.

## Release the core

The next core release is normally created from a clean `main` checkout with:

```bash
./scripts/publish_release_tag.sh X.Y.Z --push
```

Omit `X.Y.Z` to use the next patch version reported by
`scripts/next_release_version.sh`. The helper updates the package floors in the
sibling `pydevices-examples/requirements.txt` when needed, commits that change, creates
an annotated `vX.Y.Z` tag, and pushes it.

The tag starts `.github/workflows/publish-pydevices.yml`. Its jobs:

1. Build and upload the six core TestPyPI distributions.
2. Build and upload `pydevices` and `pydevices-desktop`.
3. Sync canonical sources and manifests to
   `PyDevices/mip` under `micropython/pydevices/`.
4. Compile `.mpy` artifacts, package `.py` sources, build the MIP index manifests, and publish to the `gh-pages` branch.


The workflow requires repository authentication secrets for package uploads and fork syncing.

Before tagging, run the unit tests and the publisher in a temporary/staging
mode, confirm the `micropython-lib` sync diff, and make sure both this repo and
the sibling `pydevices-examples` checkout are clean. Published versions cannot be
replaced on TestPyPI; use a new version to correct a release.

After publishing to TestPyPI, verify each portable distribution in a separate
environment. Add `--desktop` to exercise the SDL and pygame host stacks:

```bash
./tools/test_testpypi_standalone.sh
./tools/test_testpypi_standalone.sh --desktop
```

The companion repositories own their own tags and publishing workflows. Their
`docs/publishing.md` files describe any additional native-wheel build matrix.

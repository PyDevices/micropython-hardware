# Publishing

`micropython-hardware` is the canonical source and release owner for the
portable PyDevices core. A single release tag publishes the core packages to
TestPyPI, syncs their unprefixed MIP packages into the PyDevices
`micropython-lib` fork, and rebuilds the PyDevices MIP index.

`pydisplay` is the examples and integration showcase. It consumes these
packages, but does not publish them.

## Package names

TestPyPI distributions use the `pydevices-` namespace. Python imports and MIP
package names stay short and unprefixed, matching normal MicroPython library
conventions.

| Canonical source | TestPyPI distribution | Python import / MIP name |
|---|---|---|
| `drivers/display/displaydev/` | `pydevices-displaydev` | `displaydev` |
| `drivers/audio/audiodev/` | `pydevices-audiodev` | `audiodev` |
| `lib/eventsys/` | `pydevices-eventsys` | `eventsys` |
| `lib/multimer/` | `pydevices-multimer` | `multimer` |
| `lib/events.py` | `pydevices-events` | `events` |
| `lib/keys.py` | `pydevices-keys` | `keys` |
| `board_configs/desktop/` plus shared sources | `pydevices-desktop` | `board_config` and its dependencies |

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
  pydevices-displaydev pydevices-audiodev pydevices-desktop
```

Install `pydevices-eventsys` only when the application wants that event
controller. See [install-workflows.md](install-workflows.md) for board-config
and verification examples.

## Install with MIP

MIP packages are published without the `pydevices-` prefix at:

```text
https://PyDevices.github.io/micropython-lib/mip/PyDevices
```

For example:

```python
import mip

mip.install(
    "displaydev",
    index="https://PyDevices.github.io/micropython-lib/mip/PyDevices",
)
```

Board package manifests normally declare their own driver and library
dependencies. They intentionally do not declare `eventsys`; the application
owns that choice and its lifecycle.

## Release the core

The next core release is normally created from a clean `main` checkout with:

```bash
./scripts/publish_release_tag.sh X.Y.Z --push
```

Omit `X.Y.Z` to use the next patch version reported by
`scripts/next_release_version.sh`. The helper updates the package floors in the
sibling `pydisplay/requirements.txt` when needed, commits that change, creates
an annotated `vX.Y.Z` tag, and pushes it.

The tag starts `.github/workflows/publish-pydevices.yml`. Its jobs:

1. Build and upload the six core TestPyPI distributions.
2. Build and upload `pydevices-desktop`.
3. Sync canonical sources and manifests to
   `PyDevices/micropython-lib` under `micropython/pydevices/`.
4. Build and publish the MIP index to the `gh-pages` branch.

The workflow requires these repository secrets:

- `TESTPYPI_API_TOKEN` for TestPyPI uploads.
- `MICROPYTHON_LIB_DEPLOY_TOKEN` for updating the fork and its Pages branch.

Before tagging, run the unit tests and the publisher in a temporary/staging
mode, confirm the `micropython-lib` sync diff, and make sure both this repo and
the sibling `pydisplay` checkout are clean. Published versions cannot be
replaced on TestPyPI; use a new version to correct a release.

The companion repositories own their own tags and publishing workflows. Their
`docs/publishing.md` files describe any additional native-wheel build matrix.

"""Freeze the core PyDevices packages from their canonical source tree."""

if 0:

    def package(*args, **kwargs):
        pass

    def module(*args, **kwargs):
        pass


package("displaydev", base_path="./drivers/display", opt=3)  # type: ignore[name-defined]  # noqa: PGH003
package("audiodev", base_path="./drivers/audio", opt=3)  # type: ignore[name-defined]  # noqa: PGH003
package("appdev", base_path="./lib", opt=3)  # type: ignore[name-defined]  # noqa: PGH003
package("multimer", base_path="./lib", opt=3)  # type: ignore[name-defined]  # noqa: PGH003
module("events.py", base_path="./lib", opt=3)  # type: ignore[name-defined]  # noqa: PGH003
module("keys.py", base_path="./lib", opt=3)  # type: ignore[name-defined]  # noqa: PGH003

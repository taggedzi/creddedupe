"""
Credential CSV deduplication helpers.

Core functionality is exposed via :func:`dedupe_csv_file` and a simple Qt6 GUI
is available in :mod:`cred_dedupe.gui`.
"""

from importlib.metadata import PackageNotFoundError, version as _dist_version

from .core import dedupe_csv_file

try:
    # Canonical version is defined in pyproject.toml (PEP 621).
    __version__ = _dist_version("creddedupe")
except PackageNotFoundError:
    # When running directly from a source tree without installation,
    # fall back to a local version marker. Keep this value in sync with
    # the version declared in pyproject.toml so frozen builds (e.g. via
    # PyInstaller) report the correct version.
    __version__ = "1.0.2"

__all__ = ["dedupe_csv_file", "__version__"]

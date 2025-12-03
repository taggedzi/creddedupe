"""
Credential CSV deduplication helpers.

Core functionality is exposed via :func:`dedupe_csv_file` and a simple Qt6 GUI
is available in :mod:`cred_dedupe.gui`.
"""

from pathlib import Path
import sys

from importlib.metadata import PackageNotFoundError, version as _dist_version

from .core import dedupe_csv_file


def _find_pyproject() -> Path | None:
    """Locate pyproject.toml both in source and frozen bundles."""
    candidates = []

    # Source / editable install: walk up from this file.
    here = Path(__file__).resolve()
    candidates.append(here.parents[2] / "pyproject.toml")

    # PyInstaller bundle: data files live under sys._MEIPASS.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        candidates.append(Path(meipass) / "pyproject.toml")

    for path in candidates:
        if path.is_file():
            return path
    return None


try:
    # Canonical version is defined in pyproject.toml (PEP 621) when installed
    # as a distribution.
    __version__ = _dist_version("creddedupe")
except PackageNotFoundError:
    # Fallback for source tree runs or frozen binaries: read pyproject.toml
    # if we can find it (single source of truth for the version).
    pyproject_path = _find_pyproject()
    if pyproject_path is not None:
        try:  # Python 3.11+
            import tomllib  # type: ignore[attr-defined]
        except ModuleNotFoundError:  # pragma: no cover - older Python
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ModuleNotFoundError:  # pragma: no cover - no TOML parser
                __version__ = "0+unknown"
            else:
                try:
                    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
                    __version__ = data["project"]["version"]
                except Exception:  # pragma: no cover - read/parse issues
                    __version__ = "0+unknown"
        else:
            try:
                data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
                __version__ = data["project"]["version"]
            except Exception:  # pragma: no cover - read/parse issues
                __version__ = "0+unknown"
    else:
        __version__ = "0+unknown"


__all__ = ["dedupe_csv_file", "__version__"]

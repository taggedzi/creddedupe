from __future__ import annotations

from pathlib import Path
import os
import sys

"""
Helper entrypoint to build a Windows GUI executable using PyInstaller.

This is a convenience wrapper so you can run:

    pip install -e .[dev]
    creddedupe-build-win

and get a `dist/CredDedupe/CredDedupe.exe` build that matches
the instructions in the README.
"""


def main() -> int:
    try:
        from PyInstaller.__main__ import run as pyinstaller_run
    except Exception as exc:  # pragma: no cover - runtime guard
        print("PyInstaller is required to build the Windows binary.", file=sys.stderr)
        print("Install dev dependencies with:", file=sys.stderr)
        print("  pip install -e .[dev]", file=sys.stderr)
        print(f"Underlying error: {exc}", file=sys.stderr)
        return 1

    # Assume we are being run from the project root when building locally.
    project_root = Path.cwd()
    package_dir = project_root / "src" / "cred_dedupe"
    # Look for the icon only in the packaged assets directory; if it is
    # missing there, proceed without a custom icon so that tests can simulate
    # the warning path by removing this single file.
    icon_candidates = [package_dir / "assets" / "creddedupe.ico"]
    icon_path = icon_candidates[0] if icon_candidates[0].is_file() else None
    script_path = project_root / "run_creddedupe_gui.py"
    pyproject_path = project_root / "pyproject.toml"

    if icon_path is None:
        print(
            "Warning: icon file not found at any of:\n"
            + "\n".join(f"  - {p}" for p in icon_candidates)
            + "\nThe build will proceed without a custom icon.",
            file=sys.stderr,
        )
        icon_arg = []
    else:
        icon_arg = ["--icon", str(icon_path)]

    # Basic PyInstaller arguments.
    args = [
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "CredDedupe",
        *icon_arg,
        str(script_path),
    ]

    # Ensure pyproject.toml and the GUI icon are bundled as data files so
    # the frozen application can still discover its version and set a
    # window icon at runtime.
    data_args = []
    if pyproject_path.is_file():
        data_args += [
            "--add-data",
            f"{pyproject_path}{os.pathsep}.",
        ]
    if icon_path is not None:
        # Place the icon where cred_dedupe.gui expects it:
        # <resource_root>/cred_dedupe/assets/creddedupe.ico
        data_args += [
            "--add-data",
            f"{icon_path}{os.pathsep}cred_dedupe{os.path.sep}assets",
        ]

    args = [*data_args, *args]

    pyinstaller_run(args)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())

#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Add SPDX-License-Identifier headers to Python source files.

- Inserts:  # SPDX-License-Identifier: MIT
- Skips files that already contain an SPDX header.
- Handles shebang lines correctly (puts SPDX immediately after shebang).
- Skips common non-source dirs like .git, venv, dist, build by default.

Run from the repo root:
    python tools/add_spdx_headers.py

Optionally:
    python tools/add_spdx_headers.py --dry-run
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

SPDX_LINE = "# SPDX-License-Identifier: MIT"
FILE_EXTENSIONS = {".py"}

# Directories to skip entirely (relative to repo root)
DEFAULT_EXCLUDED_DIRS = {
    ".nox",
    ".ruff_cache",
    "assets",
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
}

# Specific paths (relative to repo root) you never want to touch
DEFAULT_EXCLUDED_FILES = {
    # Example: "src/third_party/some_vendor_file.py"
}


def find_source_files(
    root: Path,
    excluded_dirs: set[str],
    excluded_files: set[str],
    exts: set[str],
) -> Iterable[Path]:
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)

        # Skip unwanted directories
        dirnames[:] = [
            d for d in dirnames
            if d not in excluded_dirs
        ]

        for name in filenames:
            path = Path(dirpath) / name
            rel_path_str = str(path.relative_to(root)).replace("\\", "/")

            if rel_path_str in excluded_files:
                continue

            if path.suffix.lower() in exts:
                yield path


def file_has_spdx(path: Path) -> bool:
    """Return True if the file already contains an SPDX-License-Identifier line."""
    try:
        with path.open("r", encoding="utf-8") as f:
            for _ in range(10):  # only scan first ~10 lines
                line = f.readline()
                if not line:
                    break
                if "SPDX-License-Identifier" in line:
                    return True
    except UnicodeDecodeError:
        # Skip non-UTF-8 files
        return True
    return False


def add_spdx_header(path: Path, dry_run: bool = False) -> bool:
    """
    Insert SPDX header into the file if missing.
    Returns True if a change would be made (or was made if not dry_run).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Don't touch non-UTF-8 files
        return False

    if SPDX_LINE in text:
        return False

    lines = text.splitlines(keepends=True)
    if not lines:
        # Empty file: just add SPDX line
        new_lines = [SPDX_LINE + "\n"]
    else:
        # Check for shebang in first line
        if lines[0].startswith("#!"):
            # Insert SPDX after shebang
            new_lines = [lines[0], SPDX_LINE + "\n"]
            # If there isn't a blank line after SPDX, add one for readability
            if len(lines) > 1 and lines[1].strip():
                new_lines.append("\n")
            new_lines.extend(lines[1:])
        else:
            # No shebang: put SPDX at very top
            new_lines = [SPDX_LINE + "\n"]
            if lines and lines[0].strip():
                new_lines.append("\n")
            new_lines.extend(lines)

    new_text = "".join(new_lines)
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add SPDX-License-Identifier: MIT headers to Python source files."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Project root (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be modified, but don't write changes.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include tests/ directory as well (default: yes, unless excluded).",
    )

    args = parser.parse_args()
    root = Path(args.root).resolve()

    excluded_dirs = set(DEFAULT_EXCLUDED_DIRS)
    excluded_files = set(DEFAULT_EXCLUDED_FILES)

    # If you decide you *never* want to touch tests, you can add "tests" here:
    if not args.include_tests:
        # comment this out if you *do* want tests by default
        pass

    print(f"Scanning from project root: {root}")
    if args.dry_run:
        print("Dry-run mode: no files will be modified.\n")

    changed_count = 0
    skipped_count = 0

    for path in find_source_files(root, excluded_dirs, excluded_files, FILE_EXTENSIONS):
        rel = path.relative_to(root)
        if file_has_spdx(path):
            skipped_count += 1
            continue

        changed = add_spdx_header(path, dry_run=args.dry_run)
        if changed:
            changed_count += 1
            action = "WOULD add" if args.dry_run else "Added"
            print(f"{action} SPDX header -> {rel}")

    print()
    print(f"Files updated (or would be updated): {changed_count}")
    print(f"Files skipped (already had SPDX or non-UTF-8): {skipped_count}")


if __name__ == "__main__":
    main()

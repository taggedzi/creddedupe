# SPDX-License-Identifier: MIT
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


APP_TEMP_PREFIX = "creddedupe_"


def create_app_temp_dir() -> str:
    return tempfile.mkdtemp(prefix=APP_TEMP_PREFIX)


def cleanup_app_temp_dir(path: str | Path) -> None:
    try:
        shutil.rmtree(path)
    except Exception:
        # Best-effort; do not crash the app on cleanup failure.
        pass


__all__ = ["APP_TEMP_PREFIX", "create_app_temp_dir", "cleanup_app_temp_dir"]


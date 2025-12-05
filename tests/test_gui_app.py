# SPDX-License-Identifier: MIT

from __future__ import annotations


def test_gui_app_imports() -> None:
    # Basic smoke test to ensure the Qt GUI module is importable.
    import cred_dedupe.gui_app  # noqa: F401


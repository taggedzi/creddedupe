# SPDX-License-Identifier: MIT

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from cred_dedupe import build_win


def _install_fake_pyinstaller(monkeypatch: pytest.MonkeyPatch, calls: list[list[str]]) -> None:
    fake_mod = types.ModuleType("PyInstaller.__main__")

    def fake_run(args: list[str]) -> None:
        calls.append(args)

    fake_mod.run = fake_run  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "PyInstaller.__main__", fake_mod)


def test_build_win_with_icon(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Ensure the icon path exists so the helper passes it through.
    project_root = Path(__file__).resolve().parents[1]
    package_dir = project_root / "src" / "cred_dedupe"
    icon_path = package_dir / "assets" / "creddedupe.ico"
    script_path = project_root / "run_creddedupe_gui.py"

    # Preserve original files so the test does not mutate the repo.
    original_icon: bytes | None
    if icon_path.exists():
        original_icon = icon_path.read_bytes()
    else:
        original_icon = None

    original_script: str | None
    if script_path.exists():
        original_script = script_path.read_text(encoding="utf-8")
    else:
        original_script = None

    icon_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.parent.mkdir(parents=True, exist_ok=True)

    icon_path.write_bytes(b"\0")
    script_path.write_text("print('dummy gui')\n", encoding="utf-8")

    calls: list[list[str]] = []
    _install_fake_pyinstaller(monkeypatch, calls)

    # Ensure build_win uses our expected project_root.
    monkeypatch.chdir(project_root)

    try:
        rc = build_win.main()
        assert rc == 0
        assert calls, "PyInstaller.run should have been called"

        args = calls[0]
        # Basic sanity checks on the constructed arguments.
        assert "--windowed" in args
        assert "--name" in args
        assert "CredDedupe" in args
        # Icon path should be present.
        assert str(icon_path) in args
        assert str(script_path) in args
    finally:
        # Restore previous icon state.
        if original_icon is None:
            if icon_path.exists():
                icon_path.unlink()
        else:
            icon_path.write_bytes(original_icon)

        # Restore previous script state.
        if original_script is None:
            if script_path.exists():
                script_path.unlink()
        else:
            script_path.write_text(original_script, encoding="utf-8")


def test_build_win_without_icon(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Ensure the icon path does not exist to hit the warning branch.
    project_root = Path(__file__).resolve().parents[1]
    package_dir = project_root / "src" / "cred_dedupe"
    icon_path = package_dir / "assets" / "creddedupe.ico"
    script_path = project_root / "run_creddedupe_gui.py"

    # Preserve original files so the test does not mutate the repo.
    original_icon: bytes | None
    if icon_path.exists():
        original_icon = icon_path.read_bytes()
    else:
        original_icon = None

    original_script: str | None
    if script_path.exists():
        original_script = script_path.read_text(encoding="utf-8")
    else:
        original_script = None

    if icon_path.exists():
        icon_path.unlink()
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("print('dummy gui')\n", encoding="utf-8")

    calls: list[list[str]] = []
    _install_fake_pyinstaller(monkeypatch, calls)

    # Ensure build_win uses our expected project_root.
    monkeypatch.chdir(project_root)

    try:
        rc = build_win.main()
        assert rc == 0
        captured = capsys.readouterr()
        assert "Warning: icon file not found" in captured.err

        assert calls, "PyInstaller.run should have been called"
        args = calls[0]
        # No --icon argument should be present when the icon file is missing.
        assert "--icon" not in args
        # Script path should still be present.
        assert str(script_path) in args
    finally:
        # Restore previous icon state.
        if original_icon is None:
            if icon_path.exists():
                icon_path.unlink()
        else:
            icon_path.write_bytes(original_icon)

        # Restore previous script state.
        if original_script is None:
            if script_path.exists():
                script_path.unlink()
        else:
            script_path.write_text(original_script, encoding="utf-8")

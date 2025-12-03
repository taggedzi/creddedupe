from __future__ import annotations

import csv
from pathlib import Path

import pytest

import importlib
import importlib.metadata

from cred_dedupe import __version__
from cred_dedupe.core import (
    CSV_OUTPUT_COLUMNS,
    DedupeConfig,
    Entry,
    _normalize_domain,
    _normalize_login,
    _parse_timestamp,
    dedupe_entries,
    dedupe_csv_file,
    main as core_main,
)


def test_version_is_non_empty() -> None:
    assert isinstance(__version__, str)
    assert __version__


def test_version_fallback_when_package_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate the distribution metadata not being available.
    def fail_version(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError()

    monkeypatch.setattr(importlib.metadata, "version", fail_version)

    import cred_dedupe  # noqa: F401

    reloaded = importlib.reload(cred_dedupe)

    # Ensure the fallback version stays in sync with pyproject.toml.
    try:  # Python 3.11+
        import tomllib  # type: ignore[attr-defined]
    except ModuleNotFoundError:  # pragma: no cover - older Python
        import tomli as tomllib  # type: ignore[no-redef]

    project_root = Path(__file__).resolve().parents[1]
    pyproject = project_root / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    expected_version = data["project"]["version"]

    assert reloaded.__version__ == expected_version


def test_normalize_domain_variants() -> None:
    assert _normalize_domain("https://Example.com/login") == "example.com"
    assert _normalize_domain("http://www.Example.com/path") == "example.com"
    assert _normalize_domain("example.com") == "example.com"
    assert _normalize_domain("") == ""


def test_normalize_login_email_username_equivalence() -> None:
    cfg = DedupeConfig(treat_email_username_equivalent=True)
    entry = Entry(username="", email="USER@Example.com")
    assert _normalize_login(entry, cfg) == "user@example.com"

    cfg2 = DedupeConfig(treat_email_username_equivalent=False)
    entry2 = Entry(username="UserName", email="different@example.com")
    assert _normalize_login(entry2, cfg2) == "username"


def _make_entry(
    *,
    url: str = "",
    name: str = "",
    email: str = "",
    username: str = "",
    password: str = "",
    note: str = "",
    modify: str = "",
) -> Entry:
    cfg = DedupeConfig()
    e = Entry(
        url=url,
        name=name,
        email=email,
        username=username,
        password=password,
        note=note,
        modifyTime=modify,
    )
    e.canonical_domain = _normalize_domain(e.url)
    e.login_id = _normalize_login(e, cfg)
    return e


def test_dedupe_strict_vs_allow_different_passwords() -> None:
    e1 = _make_entry(
        url="https://example.com/login",
        username="user",
        password="one",
        note="first",
        modify="100",
    )
    e2 = _make_entry(
        url="https://www.example.com/login",
        username="user",
        password="two",
        note="second",
        modify="200",
    )

    # Strict mode: passwords differ -> no merge.
    strict_cfg = DedupeConfig(strict_password_match=True)
    result_strict, stats_strict = dedupe_entries([e1, e2], strict_cfg)
    assert len(result_strict) == 2
    assert stats_strict.merged_groups == 0

    # Loose mode: ignore password in grouping key -> merge.
    loose_cfg = DedupeConfig(strict_password_match=False)
    result_loose, stats_loose = dedupe_entries([e1, e2], loose_cfg)
    assert len(result_loose) == 1
    assert stats_loose.merged_groups == 1
    merged = result_loose[0]

    # Newer modifyTime should win for primary fields.
    assert merged.password == "two"
    # Both notes should appear in some form.
    assert "first" in merged.note
    assert "second" in merged.note
    # Alternative passwords section should be added.
    assert "Alternative passwords" in merged.note


def test_merge_group_empty_raises() -> None:
    with pytest.raises(ValueError):
        # type: ignore[arg-type] - intentionally wrong type for edge case
        from cred_dedupe.core import _merge_group

        _merge_group([])


def test_skipped_row_when_no_identifiers() -> None:
    # No login_id, no URL/domain, and empty name -> treated as ungrouped.
    cfg = DedupeConfig()
    e = Entry(password="secret")
    e.canonical_domain = ""
    e.login_id = ""

    result, stats = dedupe_entries([e], cfg)
    assert len(result) == 1
    assert stats.skipped_rows == 1


def test_dedupe_entries_uses_default_config_when_none_provided() -> None:
    # Two identical entries should be merged when using default config.
    e1 = _make_entry(
        url="https://example.com",
        username="user",
        password="pass",
        note="a",
    )
    e2 = _make_entry(
        url="https://example.com",
        username="user",
        password="pass",
        note="b",
    )

    result, stats = dedupe_entries([e1, e2], cfg=None)
    assert len(result) == 1
    assert stats.merged_groups == 1


def test_parse_timestamp_various_formats() -> None:
    # Numeric
    assert _parse_timestamp("123.5") == pytest.approx(123.5)
    # ISO with milliseconds
    iso_ms = "2024-01-02T03:04:05.123Z"
    iso_s = "2024-01-02T03:04:05Z"
    # ms version should be slightly greater than seconds-only version.
    assert _parse_timestamp(iso_ms) > _parse_timestamp(iso_s)
    # Empty / invalid -> 0.0
    assert _parse_timestamp("") == 0.0
    assert _parse_timestamp("not-a-timestamp") == 0.0


def test_dedupe_csv_file_roundtrip(tmp_path: Path) -> None:
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"

    rows = [
        {
            "type": "login",
            "name": "Example",
            "url": "https://example.com/login",
            "email": "user@example.com",
            "username": "user",
            "password": "pass",
            "note": "note1",
            "totp": "",
            "createTime": "1",
            "modifyTime": "10",
            "vault": "Default",
        },
        {
            "type": "login",
            "name": "Example site",
            "url": "http://www.example.com/login",
            "email": "",
            "username": "user",
            "password": "pass",
            "note": "note2",
            "totp": "",
            "createTime": "2",
            "modifyTime": "20",
            "vault": "Imported",
        },
    ]

    with input_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    cfg = DedupeConfig(strict_password_match=True)
    stats = dedupe_csv_file(input_path, output_path, cfg)

    assert stats.input_count == 2
    assert stats.output_count == 1
    assert stats.merged_groups == 1

    with output_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == CSV_OUTPUT_COLUMNS
        merged_rows = list(reader)

    assert len(merged_rows) == 1
    merged = merged_rows[0]
    # Should keep password and username.
    assert merged["password"] == "pass"
    assert merged["username"] == "user"
    # Notes from both rows should be preserved somewhere.
    assert "note1" in merged["note"]
    assert "note2" in merged["note"]


def test_dedupe_csv_file_missing_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"

    # Omit some required columns.
    with input_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "url"])
        writer.writerow(["Example", "https://example.com"])

    with pytest.raises(ValueError):
        dedupe_csv_file(input_path, output_path, DedupeConfig())


def test_cli_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.csv"
    rows = [
        {
            "type": "login",
            "name": "Example",
            "url": "https://example.com/login",
            "email": "",
            "username": "user",
            "password": "pass",
            "note": "",
            "totp": "",
            "createTime": "1",
            "modifyTime": "10",
            "vault": "Default",
        }
    ]
    with input_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    rc = core_main([str(input_path), "-o", str(tmp_path / "out.csv")])
    captured = capsys.readouterr()
    assert rc == 0
    assert "Processed 1 rows" in captured.out
    assert "Output written to" in captured.out


def test_cli_main_missing_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "does-not-exist.csv"
    with pytest.raises(SystemExit):
        core_main([str(missing)])


def test_cli_main_default_output_path(tmp_path: Path) -> None:
    input_path = tmp_path / "input.csv"
    rows = [
        {
            "type": "login",
            "name": "Example",
            "url": "https://example.com/login",
            "email": "",
            "username": "user",
            "password": "pass",
            "note": "",
            "totp": "",
            "createTime": "1",
            "modifyTime": "10",
            "vault": "Default",
        }
    ]
    with input_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    rc = core_main([str(input_path)])
    assert rc == 0

    expected_output = input_path.with_name(input_path.stem + "_deduped" + input_path.suffix)
    assert expected_output.is_file()

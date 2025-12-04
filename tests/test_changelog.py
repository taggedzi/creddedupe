from __future__ import annotations

import json
from pathlib import Path

from cred_dedupe.changelog import (
    ChangeEntry,
    ChangeLog,
    log_discard_manual,
    log_manual_merge,
    log_removed_exact,
    save_changelog,
    sha256_file,
)


def test_sha256_file_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("hello", encoding="utf-8")
    digest = sha256_file(path)

    # Known SHA-256 for "hello"
    assert digest == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_changelog_save_and_structure(tmp_path: Path) -> None:
    log = ChangeLog(
        original_file="input.csv",
        output_file="output.csv",
        original_hash_sha256="orig",
        output_hash_sha256="out",
    )

    log_removed_exact(log, group_index=0, kept_id="id1", removed_ids=["id2", "id3"])
    log_manual_merge(log, group_index=1, kept_id="id4", merged_from_ids=["id5"])
    log_discard_manual(log, group_index=2, discarded_ids=["id6"])

    out_path = tmp_path / "changelog.json"
    save_changelog(log, out_path)

    data = json.loads(out_path.read_text(encoding="utf-8"))

    assert data["original_file"] == "input.csv"
    assert data["output_file"] == "output.csv"
    assert data["original_hash_sha256"] == "orig"
    assert data["output_hash_sha256"] == "out"

    entries = data["entries"]
    assert len(entries) == 3
    actions = {e["action"] for e in entries}
    assert actions == {"remove_exact", "merge", "discard_manual"}


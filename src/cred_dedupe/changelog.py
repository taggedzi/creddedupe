from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ChangeEntry:
    timestamp_ms: int
    action: str  # "remove_exact", "merge", "discard_manual", etc.
    details: Dict[str, Any]


@dataclass
class ChangeLog:
    original_file: str
    output_file: str
    original_hash_sha256: str
    output_hash_sha256: str
    entries: List[ChangeEntry] = field(default_factory=list)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _now_ms() -> int:
    return int(time.time() * 1000)


def log_removed_exact(
    log: ChangeLog,
    group_index: int,
    kept_id: str,
    removed_ids: List[str],
) -> None:
    log.entries.append(
        ChangeEntry(
            timestamp_ms=_now_ms(),
            action="remove_exact",
            details={
                "group_index": group_index,
                "kept_internal_id": kept_id,
                "removed_internal_ids": removed_ids,
            },
        )
    )


def log_manual_merge(
    log: ChangeLog,
    group_index: int,
    kept_id: str,
    merged_from_ids: List[str],
) -> None:
    log.entries.append(
        ChangeEntry(
            timestamp_ms=_now_ms(),
            action="merge",
            details={
                "group_index": group_index,
                "kept_internal_id": kept_id,
                "merged_from_internal_ids": merged_from_ids,
            },
        )
    )


def log_discard_manual(
    log: ChangeLog,
    group_index: int,
    discarded_ids: List[str],
) -> None:
    log.entries.append(
        ChangeEntry(
            timestamp_ms=_now_ms(),
            action="discard_manual",
            details={
                "group_index": group_index,
                "discarded_internal_ids": discarded_ids,
            },
        )
    )


def save_changelog(log: ChangeLog, path: str | Path) -> None:
    data = {
        "original_file": log.original_file,
        "output_file": log.output_file,
        "original_hash_sha256": log.original_hash_sha256,
        "output_hash_sha256": log.output_hash_sha256,
        "entries": [
            {
                "timestamp_ms": entry.timestamp_ms,
                "action": entry.action,
                "details": entry.details,
            }
            for entry in log.entries
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


__all__ = [
    "ChangeEntry",
    "ChangeLog",
    "sha256_file",
    "log_removed_exact",
    "log_manual_merge",
    "log_discard_manual",
    "save_changelog",
]


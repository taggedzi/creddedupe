from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional

from .model import VaultItem


@dataclass
class MergeFieldDecision:
    field_name: str
    value_a: Optional[str]
    value_b: Optional[str]
    chosen_source: str  # "a", "b", or "custom"
    chosen_value: Optional[str]


@dataclass
class MergeCandidate:
    """Represents a pair (or more) of near-duplicate items to be merged."""

    items: List[VaultItem]
    primary_index: int = 0


MERGEABLE_FIELDS = (
    "title",
    "username",
    "password",
    "primary_url",
    "notes",
    "folder",
    "favorite",
    "totp_uri",
    "totp_secret",
)


def merge_items(
    a: VaultItem,
    b: VaultItem,
    decisions: Dict[str, Dict[str, Optional[str]]],
) -> VaultItem:
    """
    Merge two VaultItems using field-level decisions.

    decisions: mapping from field_name -> {
        "source": "a" | "b" | "custom",
        "value": Optional[str]  # required if source == "custom"
    }

    - For fields not in MERGEABLE_FIELDS, copy from `a` by default.
    - Preserve a/source metadata (source, source_id) by default.
    - Tags are unified (set union).
    - Extras are merged with `b` overriding on key conflicts.
    """
    merged = replace(a)

    for field_name in MERGEABLE_FIELDS:
        decision = decisions.get(field_name)
        if not decision:
            continue

        src = decision.get("source")
        if src == "a":
            setattr(merged, field_name, getattr(a, field_name))
        elif src == "b":
            setattr(merged, field_name, getattr(b, field_name))
        elif src == "custom":
            setattr(merged, field_name, decision.get("value"))

    merged.tags = sorted(set(a.tags) | set(b.tags))
    merged.extra = {**a.extra, **b.extra}

    return merged


__all__ = [
    "MergeFieldDecision",
    "MergeCandidate",
    "MERGEABLE_FIELDS",
    "merge_items",
]


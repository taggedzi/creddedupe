from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .model import VaultItem
from .utils import normalize_url


EXACT_DUPLICATE_FIELDS: Tuple[str, ...] = (
    "item_type",
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


def is_exact_duplicate(a: VaultItem, b: VaultItem) -> bool:
    """
    Return True if two VaultItem objects are considered EXACT duplicates.

    - Compare core fields defined in EXACT_DUPLICATE_FIELDS.
    - Ignore timestamps (created_at, updated_at), source, source_id, tags,
      extra, secondary_urls.
    - This is deliberately conservative: only items that truly match on all
      key fields are auto-removed.
    """
    for field_name in EXACT_DUPLICATE_FIELDS:
        if getattr(a, field_name) != getattr(b, field_name):
            return False
    return True


@dataclass
class DedupeResult:
    kept: List[VaultItem]
    removed_exact: List[VaultItem]
    exact_groups: List[List[VaultItem]]
    near_duplicate_groups: List[List[VaultItem]]


def _dedupe_key(item: VaultItem) -> Tuple[str, str]:
    """
    Build a grouping key for deduplication:
    - normalized URL (using normalize_url)
    - username
    """
    url = item.primary_url or ""
    norm_url = normalize_url(url) or ""
    return (norm_url, item.username)


def dedupe_items(items: Iterable[VaultItem]) -> DedupeResult:
    """
    Split items into:
      - kept: items that remain after automatic exact-duplicate removal
      - removed_exact: items that were auto-removed as exact duplicates
      - exact_groups: groups of items that are exact duplicates of each other
      - near_duplicate_groups: groups that share a dedupe key (domain+username)
        but are not exact duplicates (candidates for manual merge)

    Notes:
      - This function DOES NOT modify items in-place.
      - Near-duplicate groups will be handled by manual merge later.
    """
    items_list = list(items)

    groups: Dict[Tuple[str, str], List[VaultItem]] = defaultdict(list)
    for item in items_list:
        groups[_dedupe_key(item)].append(item)

    kept: List[VaultItem] = []
    removed_exact: List[VaultItem] = []
    exact_groups: List[List[VaultItem]] = []
    near_duplicate_groups: List[List[VaultItem]] = []

    for group in groups.values():
        if len(group) == 1:
            kept.append(group[0])
            continue

        remaining = list(group)
        cluster_representatives: List[VaultItem] = []

        while remaining:
            base = remaining.pop()
            cluster = [base]
            not_dupes: List[VaultItem] = []
            for other in remaining:
                if is_exact_duplicate(base, other):
                    cluster.append(other)
                else:
                    not_dupes.append(other)
            remaining = not_dupes

            if len(cluster) > 1:
                exact_groups.append(cluster)
                cluster_representatives.append(cluster[0])
                kept.append(cluster[0])
                removed_exact.extend(cluster[1:])
            else:
                # singleton; keep as-is
                kept.append(base)
                cluster_representatives.append(base)

        # Any key-group with more than one distinct representative contains
        # potential near-duplicates.
        unique_reps: List[VaultItem] = []
        seen_ids = set()
        for item in cluster_representatives:
            oid = id(item)
            if oid not in seen_ids:
                seen_ids.add(oid)
                unique_reps.append(item)

        if len(unique_reps) > 1:
            near_duplicate_groups.append(unique_reps)

    # De-duplicate kept list by object identity.
    seen_ids_all = set()
    unique_kept: List[VaultItem] = []
    for item in kept:
        oid = id(item)
        if oid not in seen_ids_all:
            seen_ids_all.add(oid)
            unique_kept.append(item)

    return DedupeResult(
        kept=unique_kept,
        removed_exact=removed_exact,
        exact_groups=exact_groups,
        near_duplicate_groups=near_duplicate_groups,
    )


__all__ = [
    "EXACT_DUPLICATE_FIELDS",
    "is_exact_duplicate",
    "DedupeResult",
    "dedupe_items",
]


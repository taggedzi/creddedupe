from __future__ import annotations

from typing import Iterable, List, Tuple

import hashlib
from collections import defaultdict

from .model import VaultItem


def _mask_secret(value: str | None) -> str:
    if not value:
        return "(empty)"
    return f"******** (len={len(value)})"


def _format_timestamp(epoch_ms: int | None) -> str:
    if not epoch_ms:
        return "(unknown)"
    try:
        from datetime import datetime, timezone

        dt = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return "(unknown)"


def score_vault_item(item: VaultItem) -> Tuple[int, int]:
    """Score a VaultItem for \"best\" selection within a group.

    Primary: latest updated_at/created_at timestamp.
    Secondary: number of non-empty core fields.
    """
    ts = item.updated_at or item.created_at or 0
    non_empty = 0
    for value in (
        item.title,
        item.username,
        item.password,
        item.primary_url,
        item.notes,
        item.folder,
        item.totp_uri,
        item.totp_secret,
    ):
        if value:
            non_empty += 1
    return ts, non_empty


def _item_key(item: VaultItem) -> str:
    """Return a stable key for mapping items within a group."""
    return item.internal_id or f"obj-{id(item)}"


def _compute_password_fingerprints(
    group: List[VaultItem],
) -> dict[str, dict]:
    """
    Compute short, non-reversible password fingerprints for display only.

    Returns:
        key -> {
            "fingerprint": str,  # hex prefix or "(none)"
            "matches": list[str],  # keys of items with same fingerprint (excluding self)
        }
    """
    id_to_fp: dict[str, str] = {}
    for item in group:
        key = _item_key(item)
        pwd = item.password or ""
        if not pwd:
            fp = "(none)"
        else:
            h = hashlib.sha256(pwd.encode("utf-8")).hexdigest()
            fp = h[:8]
        id_to_fp[key] = fp

    fp_to_ids: dict[str, List[str]] = defaultdict(list)
    for internal_id, fp in id_to_fp.items():
        fp_to_ids[fp].append(internal_id)

    result: dict[str, dict] = {}
    for internal_id, fp in id_to_fp.items():
        peers = [i for i in fp_to_ids[fp] if i != internal_id]
        result[internal_id] = {
            "fingerprint": fp,
            "matches": peers,
        }
    return result


def _choose_best_item(group: List[VaultItem]) -> VaultItem:
    scored = [(score_vault_item(item), item) for item in group]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[0][1]


def _compute_diff_flags(
    group: List[VaultItem],
    best_item: VaultItem,
) -> dict[str, List[str]]:
    """
    For each item in the group, compute short labels describing how it differs
    from the best_item.
    """
    result: dict[str, List[str]] = {}
    for item in group:
        flags: List[str] = []

        if (item.title or "") != (best_item.title or ""):
            flags.append("title")

        if (item.notes or "").strip() != (best_item.notes or "").strip():
            flags.append("notes")

        if (item.password or "") != (best_item.password or ""):
            flags.append("password")

        if getattr(item, "folder", None) != getattr(best_item, "folder", None):
            flags.append("folder")

        # Provider-specific vault name when available (e.g. Proton Pass).
        item_vault = (
            item.extra.get("proton_vault")
            if item.extra
            else None
        )
        best_vault = (
            best_item.extra.get("proton_vault")
            if best_item.extra
            else None
        )
        if item_vault != best_vault:
            flags.append("vault")

        updated = item.updated_at or item.created_at or 0
        best_updated = best_item.updated_at or best_item.created_at or 0
        if updated and best_updated:
            if updated < best_updated:
                flags.append("last changed (older)")
            elif updated > best_updated:
                flags.append("last changed (newer)")

        if not flags:
            flags.append("no differences vs best")

        result[_item_key(item)] = flags

    return result


def _prompt(prompt: str, default: str | None = None) -> str:
    if default:
        full = f"{prompt} [{default}] "
    else:
        full = f"{prompt} "
    resp = input(full).strip()
    if not resp and default is not None:
        return default
    return resp


def _prompt_choice(prompt: str, default: str, valid: set[str]) -> str:
    while True:
        resp = input(prompt).strip()
        if not resp:
            resp = default
        if resp in valid:
            return resp
        print(
            f"Invalid choice: {resp!r}. "
            f"Please choose one of: {', '.join(sorted(valid))}"
        )


def interactive_merge_near_duplicates(
    groups: List[List[VaultItem]],
    quiet: bool = False,
) -> Tuple[List[VaultItem], List[VaultItem]]:
    """
    Interactively resolve near-duplicate groups in the CLI using a simple,
    group-level decision model (no field-level merging).

    Returns:
        merged_items: list of \"survivor\" items that conceptually replace
            multiple others within their group
        discarded_items: items that the user chose to discard
    """
    merged_items: List[VaultItem] = []
    discarded_items: List[VaultItem] = []

    if not groups:
        return merged_items, discarded_items

    if not quiet:
        print(
            "Near-duplicate groups detected.\n"
            "For each group you can:\n"
            "  1) treat them as the same account and keep ONE entry\n"
            "  2) treat them as the same account and keep the BEST/NEWEST\n"
            "  3) treat them as different accounts and keep ALL\n"
            "  4) skip this group for now."
        )

    total_groups = sum(1 for g in groups if len(g) >= 2)
    printed_index = 0

    for group_index, items in enumerate(groups, start=1):
        if len(items) < 2:
            continue

        printed_index += 1
        best_item = _choose_best_item(items)
        fp_info = _compute_password_fingerprints(items)
        diff_flags = _compute_diff_flags(items, best_item)
        id_to_index = {_item_key(item): idx for idx, item in enumerate(items, start=1)}

        first = items[0]
        site = first.primary_url or "(no URL)"
        username = first.username or "(no username)"

        print(
            f"\n--- Near-duplicate group {printed_index}/{total_groups} "
            f"--------------------------------"
        )
        print(f"Site: {site}")
        print(f"Username: {username}\n")

        for idx, item in enumerate(items, start=1):
            is_best = item is best_item
            rec_label = " [RECOMMENDED]" if is_best else ""
            key = _item_key(item)
            fp_data = fp_info.get(key, {})
            fp = fp_data.get("fingerprint", "(none)")
            matches = fp_data.get("matches", [])

            pwd_display = _mask_secret(item.password)
            if fp == "(none)":
                pwd_line = f"{pwd_display}  [no password set]"
            else:
                if matches:
                    match_indices = sorted(
                        id_to_index[m] for m in matches if m in id_to_index
                    )
                    match_str = ",".join(str(i) for i in match_indices)
                    pwd_line = (
                        f"{pwd_display}  [fingerprint: {fp}, matches: {match_str}]"
                    )
                else:
                    pwd_line = f"{pwd_display}  [fingerprint: {fp}]"

            notes = (item.notes or "").strip()
            if notes:
                preview = notes if len(notes) <= 60 else notes[:57] + "..."
            else:
                preview = "(empty)"

            created_str = _format_timestamp(item.created_at)
            updated_str = _format_timestamp(item.updated_at)

            flags = diff_flags.get(key, [])
            flags_str = ", ".join(flags) if flags else "(none)"

            print(
                f"[{idx}] Title: {item.title or '(no title)'}{rec_label}\n"
                f"    Password: {pwd_line}\n"
                f"    Notes: {preview}\n"
                f"    First created: {created_str}\n"
                f"    Last changed:  {updated_str}\n"
                f"    Differences vs others: {flags_str}\n"
            )

        best_index = id_to_index[_item_key(best_item)]

        print(
            "What do you want to do with this group?\n\n"
            "  1) Same account – keep ONE specific entry\n"
            f"  2) Same account – keep the BEST/NEWEST entry (recommended: #{best_index})\n"
            "  3) Different accounts – keep ALL entries\n"
            "  4) Skip this group for now\n"
        )

        choice = _prompt_choice(
            "Choice [2]: ",
            default="2",
            valid={"1", "2", "3", "4"},
        )

        if choice == "3":
            if not quiet:
                print("Keeping all entries in this group as separate accounts.")
            continue

        if choice == "4":
            if not quiet:
                print("Skipping this group; keeping all entries as-is.")
            continue

        if choice == "1":
            while True:
                idx_str = _prompt(
                    f"Enter the number of the entry to keep [1-{len(items)}]",
                    default="1",
                ).strip()
                try:
                    keep_idx = int(idx_str)
                except ValueError:
                    print("Please enter a valid integer.")
                    continue
                if 1 <= keep_idx <= len(items):
                    keep_idx -= 1
                    break
                print(f"Please enter a number between 1 and {len(items)}.")

            survivor = items[keep_idx]
        elif choice == "2":
            scored = [(score_vault_item(item), item) for item in items]
            scored.sort(key=lambda pair: pair[0], reverse=True)
            survivor = scored[0][1]
        else:
            # Should not happen due to validation.
            continue

        losers = [item for item in items if item is not survivor]

        # Attach minimal metadata for changelog and recomputation without
        # leaking any sensitive information.
        survivor_extra = dict(survivor.extra or {})
        survivor_extra.setdefault("dedupe_group_index", str(group_index))
        src_ids = []
        for item in items:
            if item.internal_id:
                src_ids.append(item.internal_id)
        if src_ids:
            survivor_extra.setdefault(
                "dedupe_merged_from_internal_ids",
                ",".join(src_ids),
            )
        survivor.extra = survivor_extra

        merged_items.append(survivor)

        for victim in losers:
            victim_extra = dict(victim.extra or {})
            victim_extra.setdefault(
                "dedupe_manual_discard_group_index",
                str(group_index),
            )
            victim.extra = victim_extra
            discarded_items.append(victim)

    return merged_items, discarded_items


def recompute_final_items(
    original_items: Iterable[VaultItem],
    merged_items: Iterable[VaultItem],
    discarded_items: Iterable[VaultItem],
) -> List[VaultItem]:
    """
    Build a final item list from:
      - original_items
      - merged_items: replacement items
      - discarded_items: items to drop

    Matching is currently done by object identity; in future this can use
    stable internal IDs.
    """
    discarded_internal_ids = {
        i.internal_id for i in discarded_items if i.internal_id
    }

    # Items that were merged are tracked via a non-sensitive metadata field on
    # the merged item; drop those originals so that the merged replacement is
    # the only copy in the final list.
    merged_source_ids: set[str] = set()
    for merged in merged_items:
        meta = merged.extra or {}
        src_ids = meta.get("dedupe_merged_from_internal_ids", "")
        if not src_ids:
            continue
        for raw in src_ids.split(","):
            ident = raw.strip()
            if ident:
                merged_source_ids.add(ident)

    result: List[VaultItem] = []
    seen_ids: set[str] = set()
    for item in original_items:
        internal_id = item.internal_id
        if internal_id and internal_id in discarded_internal_ids:
            continue
        if internal_id and internal_id in merged_source_ids:
            continue
        result.append(item)
        if internal_id:
            seen_ids.add(internal_id)

    # Append merged items as replacements or survivors, avoiding duplicates.
    for item in merged_items:
        internal_id = item.internal_id
        if internal_id and internal_id in seen_ids:
            continue
        result.append(item)
        if internal_id:
            seen_ids.add(internal_id)

    return result


__all__ = [
    "interactive_merge_near_duplicates",
    "recompute_final_items",
    "score_vault_item",
]

# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from collections import defaultdict

from .model import VaultItem


def _mask_secret(value: str | None) -> str:
    if not value:
        return "(empty)"
    return f"******** (len={len(value)})"


def _safe_display_password(pwd: Optional[str]) -> str:
    """
    Return a safe, redacted representation of a password for console display.

    - Never returns the actual password.
    - Only indicates length, or "(empty)".
    """
    if not pwd:
        return "Password: (empty)"
    return f"Password: ******** (len={len(pwd)})"


def _safe_display_notes(notes: Optional[str], max_len: int = 60) -> str:
    """
    Return a safe preview of notes.

    - Treat notes as potentially sensitive.
    - Only show at most max_len characters.
    - Indicate if text was truncated.
    """
    if not notes:
        return "Notes: (empty)"

    stripped = notes.strip()
    if len(stripped) <= max_len:
        return f"Notes: {stripped}"

    preview = stripped[: max_len - 3] + "..."
    return f"Notes: {preview} (truncated)"


def _safe_display_totp(has_totp: bool) -> str:
    """
    Safe representation of TOTP presence.

    - Do not print the TOTP URI or secret.
    """
    if has_totp:
        return "TOTP: present"
    return "TOTP: none"


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


def _compute_password_matches(group: List["VaultItem"]) -> dict[str, List[str]]:
    """
    For a group of VaultItem, compute which entries share the same password.

    Returns:
        internal_id -> list of other internal_ids in the group that have
                       the exact same password (excluding self).

    Notes:
        - Passwords are compared directly in memory.
        - No passwords or derived values are stored, returned, or printed.
        - This is purely for in-memory grouping so we can show
          "same password as entries X,Y" vs "unique password in this group".
    """
    pw_to_ids: dict[Optional[str], List[str]] = defaultdict(list)

    for item in group:
        pw = item.password or None
        if item.internal_id is not None:
            pw_to_ids[pw].append(item.internal_id)

    matches_by_id: dict[str, List[str]] = {}
    for item in group:
        if item.internal_id is None:
            continue
        pw = item.password or None
        ids = pw_to_ids.get(pw, [])
        matches_by_id[item.internal_id] = [
            i for i in ids if i != item.internal_id
        ]

    return matches_by_id


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
        diff_flags = _compute_diff_flags(items, best_item)
        pw_matches = _compute_password_matches(items)
        id_to_index = {
            item.internal_id: idx
            for idx, item in enumerate(items, start=1)
            if item.internal_id is not None
        }

        first = items[0]
        site = first.primary_url or "(no URL)"
        username = first.username or "(no username)"

        if not quiet:
            print(
                f"\n--- Near-duplicate group {printed_index}/{total_groups} "
                f"--------------------------------"
            )
            print(f"Site: {site}")
            print(f"Username: {username}\n")

        for idx, item in enumerate(items, start=1):
            is_best = item is best_item
            rec_label = " [RECOMMENDED]" if is_best else ""

            if not quiet:
                title_str = f"[{idx}] Title: {item.title or '(no title)'}{rec_label}"

                password_str = _safe_display_password(item.password)
                if item.password:
                    same_ids = pw_matches.get(item.internal_id or "", [])
                    if same_ids:
                        same_indices = sorted(
                            id_to_index[i] for i in same_ids if i in id_to_index
                        )
                        idx_list = ",".join(str(i) for i in same_indices)
                        password_str = (
                            f"{password_str}  "
                            f"[same password as entries {idx_list}]"
                        )
                    else:
                        password_str = (
                            f"{password_str}  "
                            "[unique password in this group]"
                        )

                notes_str = _safe_display_notes(item.notes)

                created_ts = _format_timestamp(item.created_at)
                updated_ts = _format_timestamp(item.updated_at)
                created_line = f"First created: {created_ts}"
                updated_line = f"Last changed:  {updated_ts}"

                key = _item_key(item)
                flags = diff_flags.get(key, [])
                if flags and flags != ["no differences vs best"]:
                    flags_str = ", ".join(flags)
                else:
                    flags_str = "none"
                flags_line = f"Differences vs others: {flags_str}"

                # The following print block only uses sanitized display strings
                # (see _safe_display_password/_safe_display_notes/_safe_display_totp).
                # No raw passwords, TOTP secrets, or full note contents are printed.
                # codeql[clear-text-logging-of-sensitive-data]
                print(
                    f"{title_str}\n"
                    f"    {password_str}\n"
                    f"    {notes_str}\n"
                    f"    {created_line}\n"
                    f"    {updated_line}\n"
                    f"    {flags_line}\n"
                )

        best_index = id_to_index.get(
            best_item.internal_id, next(
                idx for idx, item in enumerate(items, start=1) if item is best_item
            )
        )

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

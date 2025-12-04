from __future__ import annotations

from typing import Iterable, List, Tuple

from .merge import MERGEABLE_FIELDS, merge_items
from .model import VaultItem


def _mask_value(field_name: str, value) -> str:
    if value is None:
        return ""
    text = str(value)
    if field_name in {"password", "totp_uri", "totp_secret"}:
        if not text:
            return ""
        return f"<hidden len={len(text)}>"
    return text


def _prompt(prompt: str, default: str | None = None) -> str:
    if default:
        full = f"{prompt} [{default}] "
    else:
        full = f"{prompt} "
    resp = input(full).strip()
    if not resp and default is not None:
        return default
    return resp


def interactive_merge_near_duplicates(
    groups: List[List[VaultItem]],
) -> Tuple[List[VaultItem], List[VaultItem]]:
    """
    Interactively resolve near-duplicate groups in the CLI.

    Returns:
      - merged_items: list of merged items
      - discarded_items: items that user chose to delete
    """
    merged_items: List[VaultItem] = []
    discarded_items: List[VaultItem] = []

    if not groups:
        return merged_items, discarded_items

    print(
        "Near-duplicate groups detected. You can interactively merge entries, "
        "or skip groups to keep all items."
    )

    for group_index, items in enumerate(groups, start=1):
        if len(items) < 2:
            continue

        print(f"\nGroup {group_index}:")
        for idx, item in enumerate(items, start=1):
            print(
                f"  [{idx}] title={item.title!r} "
                f"username={item.username!r} url={item.primary_url!r} "
                f"source={item.source or ''}"
            )

        answer = _prompt(
            "Merge items in this group? (y/N, s=skip group)", default="n"
        ).lower()
        if answer not in {"y", "yes"}:
            continue

        if len(items) == 2:
            a_idx, b_idx = 1, 2
        else:
            pair_text = _prompt(
                "Enter two item numbers to merge (e.g. 1 2), or press Enter to skip",
                default="",
            )
            if not pair_text:
                continue
            parts = pair_text.split()
            if len(parts) != 2:
                print("Invalid input, skipping this group.")
                continue
            try:
                a_idx = int(parts[0])
                b_idx = int(parts[1])
            except ValueError:
                print("Invalid numbers, skipping this group.")
                continue
            if not (1 <= a_idx <= len(items) and 1 <= b_idx <= len(items)):
                print("Indexes out of range, skipping this group.")
                continue
            if a_idx == b_idx:
                print("Need two different items, skipping this group.")
                continue

        a = items[a_idx - 1]
        b = items[b_idx - 1]

        print(f"\nMerging item {a_idx} (A) and {b_idx} (B):")

        decisions: dict = {}
        for field_name in MERGEABLE_FIELDS:
            val_a = getattr(a, field_name)
            val_b = getattr(b, field_name)
            if val_a == val_b:
                continue

            print(f"\nField: {field_name}")
            print(f"  A: {_mask_value(field_name, val_a)!r}")
            print(f"  B: {_mask_value(field_name, val_b)!r}")

            choice = _prompt(
                "Choose source (a/b/c=custom/s=skip field)", default="a"
            ).lower()

            if choice in {"a", "b"}:
                decisions[field_name] = {"source": choice, "value": None}
            elif choice == "c":
                custom_value = _prompt("Enter custom value", default=str(val_a or ""))
                decisions[field_name] = {
                    "source": "custom",
                    "value": custom_value,
                }
            else:
                # Skip field, keep A.
                continue

        merged = merge_items(a, b, decisions)

        print("\nMerged item summary (sensitive values hidden):")
        print(
            f"  title={merged.title!r} username={merged.username!r} "
            f"url={merged.primary_url!r} source={merged.source or ''}"
        )

        confirm = _prompt("Replace A with merged and delete B? (y/N)", default="n")
        if confirm.lower() in {"y", "yes"}:
            merged_items.append(merged)
            discarded_items.append(b)
        else:
            print("Merge cancelled for this pair; keeping originals.")

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
    discarded_ids = {id(i) for i in discarded_items}
    result: List[VaultItem] = []

    # Start from originals, drop discarded items.
    for item in original_items:
        if id(item) in discarded_ids:
            continue
        result.append(item)

    # Append merged items; callers are responsible for avoiding duplicates.
    result.extend(merged_items)
    return result


__all__ = [
    "interactive_merge_near_duplicates",
    "recompute_final_items",
]


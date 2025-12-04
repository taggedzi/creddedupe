from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List, Sequence, Tuple

from .changelog import (
    ChangeLog,
    log_discard_manual,
    log_manual_merge,
    log_removed_exact,
    save_changelog,
    sha256_file,
)
from .cli_merge import (
    interactive_merge_near_duplicates,
    recompute_final_items,
    score_vault_item,
)
from .core import print_security_warning_once
from .dedupe import DedupeResult, dedupe_items
from .detection import DetectionResult, detect_provider
from .model import VaultItem
from .plugins import ProviderFormat, get_registry, register_all_plugins
from .temp_utils import cleanup_app_temp_dir, create_app_temp_dir


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Credential deduplication CLI for cleaning password-manager and "
            "browser CSV exports."
        ),
        epilog=(
            "DISCLAIMER: This project and its author are not affiliated with, "
            "endorsed by, or sponsored by any password application."
        ),
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to input CSV export.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to output CSV that will be written.",
    )
    parser.add_argument(
        "--input-provider",
        default="auto",
        help=(
            "Input provider format. Use 'auto' to auto-detect based on CSV "
            "headers, or specify a concrete provider such as 'lastpass', "
            "'bitwarden', 'protonpass', etc."
        ),
    )
    parser.add_argument(
        "--output-provider",
        default=None,
        help=(
            "Output provider format. Defaults to the chosen input provider "
            "when omitted."
        ),
    )
    parser.add_argument(
        "--no-interactive-merge",
        action="store_true",
        help=(
            "Disable interactive merge of near-duplicate groups. When set, "
            "near-duplicates are kept as separate entries."
        ),
    )
    parser.add_argument(
        "--auto-merge-near-duplicates",
        action="store_true",
        help=(
            "Automatically resolve near-duplicate groups by keeping a single "
            "best entry (based on timestamps and data completeness) and "
            "discarding the others. No interactive prompts are shown."
        ),
    )
    parser.add_argument(
        "--changelog",
        default=None,
        help=(
            "Optional path to a JSON changelog describing non-sensitive "
            "deduplication operations."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-essential output (errors are still printed).",
    )

    return parser


def _normalize_provider_name(name: str) -> str:
    return name.strip().lower()


def _provider_name_map() -> dict[str, ProviderFormat]:
    return {
        fmt.value: fmt
        for fmt in ProviderFormat
        if fmt is not ProviderFormat.UNKNOWN
    }


def _prompt(text: str, default: str | None = None) -> str:
    if default is not None:
        full = f"{text} [{default}] "
    else:
        full = f"{text} "
    resp = input(full).strip()
    if not resp and default is not None:
        return default
    return resp


def _prompt_for_provider_interactive(
    registry_formats: List[ProviderFormat],
) -> ProviderFormat:
    name_map = _provider_name_map()
    available = [fmt for fmt in registry_formats if fmt is not ProviderFormat.UNKNOWN]
    if not available:
        raise SystemExit(
            "No provider plugins are registered; unable to choose a provider."
        )

    print("Available providers:")
    for idx, fmt in enumerate(available, start=1):
        print(f"  {idx}) {fmt.value}")

    while True:
        resp = input("Enter number or name (or 'q' to quit): ").strip().lower()
        if resp in {"q", "quit"}:
            raise SystemExit("Aborted by user.")

        if resp.isdigit():
            idx = int(resp)
            if 1 <= idx <= len(available):
                return available[idx - 1]
            print("Invalid index; please try again.")
            continue

        if resp in name_map:
            return name_map[resp]

        print("Unrecognized provider; please enter a valid number or name.")


def _print_detection_summary(result: DetectionResult) -> None:
    provider = result.provider
    if not result.matches:
        print(result.reason)
        return

    best = result.matches[0]
    print(
        f"Detected provider: {provider.value} "
        f"(confidence {result.confidence:.2f})"
    )
    print(
        "Best match: "
        f"{provider.value} "
        f"(score={best.score:.2f}, "
        f"matched_required={best.matched_required}/{best.total_required}, "
        f"matched_optional={best.matched_optional}/{best.total_optional})"
    )


def choose_input_provider(
    headers: List[str],
    registry,
    requested: str | None,
    quiet: bool = False,
) -> ProviderFormat:
    """
    Decide which ProviderFormat to use for the input CSV.

    - If requested is a specific provider name (not \"auto\"), validate it and
      return directly.
    - If requested is \"auto\" or None, run detect_provider() and optionally
      ask the user to confirm/override.
    """
    requested = _normalize_provider_name(requested or "auto")
    name_map = _provider_name_map()

    if requested != "auto":
        if requested not in name_map:
            available = ", ".join(sorted(name_map.keys()))
            raise SystemExit(
                f"Unknown input provider: {requested!r}. "
                f"Available providers: {available}"
            )
        provider = name_map[requested]
        # Ensure plugin is registered.
        try:
            registry.get(provider)
        except KeyError as exc:
            raise SystemExit(
                f"No plugin registered for requested provider: {provider.value!r}"
            ) from exc
        return provider

    # Auto-detect path.
    detection = detect_provider(headers, registry)

    if quiet:
        if detection.provider is ProviderFormat.UNKNOWN:
            raise SystemExit(
                "Unable to auto-detect provider; specify --input-provider."
            )
        return detection.provider

    if detection.provider is ProviderFormat.UNKNOWN or detection.confidence < 0.5:
        print("Could not confidently detect CSV format.")
        providers = [p.provider_type for p in registry.all_plugins()]
        return _prompt_for_provider_interactive(providers)

    # Reasonably confident detection; ask for confirmation.
    _print_detection_summary(detection)
    answer = _prompt(
        f"Use detected provider '{detection.provider.value}'? (Y/n)",
        default="y",
    ).lower()

    if answer in {"", "y", "yes"}:
        return detection.provider

    providers = [p.provider_type for p in registry.all_plugins()]
    return _prompt_for_provider_interactive(providers)


def _ensure_internal_ids(items: List[VaultItem]) -> None:
    """Populate internal_id on items that don't already have it."""
    counter = 1
    for item in items:
        if not item.internal_id:
            item.internal_id = f"item-{counter}"
            counter += 1


def _print_dedupe_summary(result: DedupeResult) -> None:
    print(f"Imported items: {len(result.kept) + len(result.removed_exact)}")
    if result.removed_exact:
        print(f"Exact duplicates removed automatically: {len(result.removed_exact)}")
    print(
        f"Near-duplicate groups needing review: "
        f"{len(result.near_duplicate_groups)}"
    )
    for idx, group in enumerate(result.near_duplicate_groups, start=1):
        if not group:
            continue
        first = group[0]
        print(
            f"  Group {idx}: "
            f"{(first.primary_url or '')!r} / {first.username!r} "
            f"– {len(group)} entries"
        )


def _export_items_to_csv(
    items: List[VaultItem],
    output_path: Path,
    provider: ProviderFormat,
) -> None:
    registry = get_registry()
    plugin = registry.get(provider)

    # Derive header order from the first exported row; this avoids requiring
    # every plugin to expose a separate export_header() API.
    header: List[str] = []
    rows: List[dict[str, str]] = []
    for item in items:
        row = plugin.export_row(item)
        rows.append(row)
        if not header:
            header = list(row.keys())

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _auto_resolve_near_duplicates(
    result: DedupeResult,
) -> Tuple[List[VaultItem], List[VaultItem]]:
    """
    Automatically resolve near-duplicate groups by keeping a single best item
    in each group and discarding the rest.

    Returns:
        merged_items: list of survivor items (one per group)
        discarded_items: items that were dropped as near-duplicates
    """
    merged_items: List[VaultItem] = []
    discarded_items: List[VaultItem] = []

    for group_index, group in enumerate(result.near_duplicate_groups, start=1):
        if not group:
            continue

        best = max(group, key=score_vault_item)

        # Attach metadata to the survivor for changelog and recomputation.
        survivor_extra = dict(best.extra or {})
        survivor_extra.setdefault("dedupe_group_index", str(group_index))
        src_ids = []
        for item in group:
            if item.internal_id:
                src_ids.append(item.internal_id)
        if src_ids:
            survivor_extra.setdefault(
                "dedupe_merged_from_internal_ids",
                ",".join(src_ids),
            )
        best.extra = survivor_extra
        merged_items.append(best)

        for item in group:
            if item is best:
                continue

            extra = dict(item.extra or {})
            extra.setdefault(
                "dedupe_manual_discard_group_index",
                str(group_index),
            )
            item.extra = extra
            discarded_items.append(item)

    return merged_items, discarded_items


def main(argv: Sequence[str] | None = None) -> int:
    """
    Main CLI entrypoint for creddedupe.

    Returns:
        0 on success, non-zero on error.
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    # Security warning (once per process).
    if not args.quiet:
        print_security_warning_once()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.is_file():
        parser.error(f"Input file not found: {input_path}")

    # Ensure all built-in provider plugins are registered.
    register_all_plugins()
    registry = get_registry()

    temp_dir = create_app_temp_dir()
    try:
        # Read header row and detect or choose provider.
        with input_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            headers: List[str] = reader.fieldnames or []
            provider = choose_input_provider(
                headers,
                registry,
                requested=args.input_provider,
                quiet=args.quiet,
            )

            plugin = registry.get(provider)
            items: List[VaultItem] = []
            for row in reader:
                items.append(plugin.import_row(row))

        _ensure_internal_ids(items)

        dedupe_result = dedupe_items(items)

        if not args.quiet:
            _print_dedupe_summary(dedupe_result)

        merged_items: List[VaultItem] = []
        discarded_items: List[VaultItem] = []

        if args.auto_merge_near_duplicates and dedupe_result.near_duplicate_groups:
            merged_items, discarded_items = _auto_resolve_near_duplicates(
                dedupe_result
            )
        elif (
            not args.no_interactive_merge and dedupe_result.near_duplicate_groups
        ):
            merged_items, discarded_items = interactive_merge_near_duplicates(
                dedupe_result.near_duplicate_groups,
                quiet=args.quiet,
            )

        final_items = recompute_final_items(
            dedupe_result.kept,
            merged_items,
            discarded_items,
        )

        # Determine output provider: explicit override or default to input
        # provider.
        if args.output_provider:
            out_name = _normalize_provider_name(args.output_provider)
            name_map = _provider_name_map()
            if out_name not in name_map:
                available = ", ".join(sorted(name_map.keys()))
                raise SystemExit(
                    f"Unknown output provider: {out_name!r}. "
                    f"Available providers: {available}"
                )
            output_provider = name_map[out_name]
        else:
            output_provider = provider

        _export_items_to_csv(final_items, output_path, output_provider)

        # Changelog (optional, non-sensitive).
        if args.changelog:
            change_log = ChangeLog(
                original_file=str(input_path),
                output_file=str(output_path),
                original_hash_sha256="",
                output_hash_sha256="",
            )

            # Exact-duplicate removals.
            for idx, group in enumerate(dedupe_result.exact_groups):
                if not group or len(group) < 2:
                    continue
                kept = group[0]
                removed = group[1:]
                kept_id = kept.internal_id or ""
                removed_ids = [item.internal_id or "" for item in removed]
                log_removed_exact(change_log, idx, kept_id, removed_ids)

            # Manual merges (metadata recorded by interactive_merge_near_duplicates).
            for merged in merged_items:
                meta = merged.extra or {}
                group_index_str = meta.get("dedupe_group_index")
                merged_from_ids_str = meta.get(
                    "dedupe_merged_from_internal_ids", ""
                )
                if not group_index_str:
                    continue
                try:
                    group_index = int(group_index_str)
                except ValueError:
                    continue

                merged_from_ids = [
                    x for x in merged_from_ids_str.split(",") if x
                ] or [merged.internal_id or ""]
                kept_id = merged.internal_id or ""
                log_manual_merge(
                    change_log,
                    group_index=group_index,
                    kept_id=kept_id,
                    merged_from_ids=merged_from_ids,
                )

            # Manual discards (non-merge).
            grouped_discards: dict[int, List[str]] = {}
            for item in discarded_items:
                meta = item.extra or {}
                group_index_str = meta.get("dedupe_manual_discard_group_index")
                if not group_index_str:
                    continue
                try:
                    gid = int(group_index_str)
                except ValueError:
                    continue
                grouped_discards.setdefault(gid, []).append(
                    item.internal_id or ""
                )

            for gid, ids in grouped_discards.items():
                if ids:
                    log_discard_manual(change_log, group_index=gid, discarded_ids=ids)

            # Populate file hashes and write the changelog file.
            change_log.original_hash_sha256 = sha256_file(input_path)
            change_log.output_hash_sha256 = sha256_file(output_path)
            save_changelog(change_log, args.changelog)

            if not args.quiet:
                print(f"Changelog written to: {args.changelog}")
                print(f"Input SHA-256:  {change_log.original_hash_sha256}")
                print(f"Output SHA-256: {change_log.output_hash_sha256}")

        if not args.quiet:
            print(f"Exported {len(final_items)} items to {output_path}")

        return 0
    finally:
        cleanup_app_temp_dir(temp_dir)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())

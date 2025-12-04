from __future__ import annotations

import argparse
import csv
import dataclasses
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse


CSV_INPUT_COLUMNS = [
    "type",
    "name",
    "url",
    "email",
    "username",
    "password",
    "note",
    "totp",
    "createTime",
    "modifyTime",
    "vault",
]

CSV_OUTPUT_COLUMNS = [
    "name",
    "url",
    "email",
    "username",
    "password",
    "note",
    "totp",
    "vault",
]


@dataclass
class Entry:
    type: str = ""
    name: str = ""
    url: str = ""
    email: str = ""
    username: str = ""
    password: str = ""
    note: str = ""
    totp: str = ""
    createTime: str = ""
    modifyTime: str = ""
    vault: str = ""

    # Computed fields (not written back to CSV)
    canonical_domain: str = ""
    login_id: str = ""


@dataclass
class DedupeConfig:
    strict_password_match: bool = True
    treat_email_username_equivalent: bool = True


@dataclass
class DedupeStats:
    input_count: int
    output_count: int
    merged_groups: int
    skipped_rows: int


def _normalize_text(value: str) -> str:
    return value.strip()


def _normalize_login(entry: Entry, cfg: DedupeConfig) -> str:
    username = _normalize_text(entry.username)
    email = _normalize_text(entry.email)

    if cfg.treat_email_username_equivalent:
        candidate = username or email
    else:
        candidate = username

    return candidate.lower()


def _normalize_domain(url: str) -> str:
    url = url.strip()
    if not url:
        return ""

    # If there is no scheme, prepend https:// for parsing purposes.
    if "://" not in url and not url.startswith("//"):
        url_to_parse = "https://" + url
    else:
        url_to_parse = url

    parsed = urlparse(url_to_parse)
    host = parsed.hostname or ""
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _parse_timestamp(value: str) -> float:
    """
    Try to interpret timestamps in a reasonably robust way.

    exports may use epoch seconds/milliseconds or ISO strings.
    We only need ordering, not exact times.
    """
    value = value.strip()
    if not value:
        return 0.0

    # Numeric formats (epoch seconds or ms).
    try:
        num = float(value)
        return num
    except ValueError:
        pass

    # A few common ISO-ish formats.
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(value, fmt)
        except ValueError:
            continue
        else:
            return dt.timestamp()

    # Fallback: preserve lexicographic ordering best-effort.
    return 0.0


def _entry_from_row(row: Dict[str, str], cfg: DedupeConfig) -> Entry:
    entry = Entry(
        type=row.get("type", "") or "",
        name=row.get("name", "") or "",
        url=row.get("url", "") or "",
        email=row.get("email", "") or "",
        username=row.get("username", "") or "",
        password=row.get("password", "") or "",
        note=row.get("note", "") or "",
        totp=row.get("totp", "") or "",
        createTime=row.get("createTime", "") or "",
        modifyTime=row.get("modifyTime", "") or "",
        vault=row.get("vault", "") or "",
    )
    entry.canonical_domain = _normalize_domain(entry.url)
    entry.login_id = _normalize_login(entry, cfg)
    return entry


def _entry_to_row(entry: Entry) -> Dict[str, str]:
    return {
        "name": entry.name,
        "url": entry.url,
        "email": entry.email,
        "username": entry.username,
        "password": entry.password,
        "note": entry.note,
        "totp": entry.totp,
        "vault": entry.vault,
    }


def _group_key(entry: Entry, cfg: DedupeConfig) -> Tuple[str, str, str]:
    """
    Build a grouping key for potential duplicates.

    We use (domain_or_name, login_id, [password]) to group.
    - domain_or_name: canonical domain if available, otherwise normalized name.
    - login_id: lowercased username/email depending on config.
    - password: either the actual password or empty string if not used.
    """
    domain_or_name = entry.canonical_domain or entry.name.strip().lower()
    login_id = entry.login_id

    if cfg.strict_password_match:
        password = entry.password
    else:
        password = ""

    return (domain_or_name, login_id, password)


def _choose_preferred_entry(entries: Sequence[Entry]) -> Entry:
    """
    Pick the entry that looks "best":
    - Newest modifyTime.
    - Then the one with the most non-empty important fields.
    """
    def score(e: Entry) -> Tuple[float, int]:
        ts = _parse_timestamp(e.modifyTime)
        non_empty = sum(
            1 for v in [
                e.url,
                e.email,
                e.username,
                e.password,
                e.note,
                e.totp,
            ]
            if v.strip()
        )
        return (ts, non_empty)

    return max(entries, key=score)


def _merge_group(entries: Sequence[Entry]) -> Entry:
    """
    Merge a group of duplicate entries into a single entry, preserving as
    much information as possible.
    """
    if not entries:
        raise ValueError("Cannot merge an empty group")

    if len(entries) == 1:
        # Nothing to merge.
        return dataclasses.replace(entries[0])

    preferred = _choose_preferred_entry(entries)
    merged = dataclasses.replace(preferred)

    # Collect distinct values for some fields.
    def distinct(field: str) -> List[str]:
        seen = []
        for e in entries:
            val = getattr(e, field, "")
            val = val.strip()
            if val and val not in seen:
                seen.append(val)
        return seen

    name_vals = distinct("name")
    url_vals = distinct("url")
    email_vals = distinct("email")
    username_vals = distinct("username")
    password_vals = distinct("password")
    note_vals = distinct("note")
    totp_vals = distinct("totp")
    vault_vals = distinct("vault")

    extras: List[str] = []

    def build_alt_label(label: str, values: List[str], chosen: str) -> None:
        alts = [v for v in values if v != chosen.strip()]
        if alts:
            extras.append(f"{label}: {', '.join(alts)}")

    build_alt_label("Alternative names", name_vals, merged.name)
    build_alt_label("Alternative URLs", url_vals, merged.url)
    build_alt_label("Alternative emails", email_vals, merged.email)
    build_alt_label("Alternative usernames", username_vals, merged.username)
    build_alt_label("Alternative passwords", password_vals, merged.password)
    build_alt_label("Alternative TOTP secrets", totp_vals, merged.totp)
    build_alt_label("Original vaults", vault_vals, merged.vault)

    # Merge notes explicitly, keeping all distinct notes.
    base_notes = [n for n in note_vals]
    merged_notes = []
    for n in base_notes:
        if n and n not in merged_notes:
            merged_notes.append(n)

    note_text = "\n\n".join(merged_notes).strip()

    if extras:
        extras_block = "Merged from duplicates:\n" + "\n".join(
            f"- {line}" for line in extras
        )
        if note_text:
            note_text = note_text + "\n\n" + extras_block
        else:
            note_text = extras_block

    merged.note = note_text

    return merged


def dedupe_entries(
    entries: Iterable[Entry],
    cfg: Optional[DedupeConfig] = None,
) -> Tuple[List[Entry], DedupeStats]:
    """
    Core deduplication routine. Takes a sequence of entries and returns a new
    list of entries plus some statistics.
    """
    if cfg is None:
        cfg = DedupeConfig()

    groups: Dict[Tuple[str, str, str], List[Entry]] = {}
    skipped = 0
    count = 0

    for entry in entries:
        count += 1

        # If we lack both a grouping identifier and a password, we keep the row
        # as-is to avoid accidental merges.
        if not entry.login_id and not entry.canonical_domain and not entry.name.strip():
            skipped += 1
            key = ("__ungrouped__", f"row-{count}", entry.password)
        else:
            key = _group_key(entry, cfg)

        groups.setdefault(key, []).append(entry)

    result: List[Entry] = []
    merged_groups = 0

    for group_entries in groups.values():
        if len(group_entries) > 1:
            merged_groups += 1
        result.append(_merge_group(group_entries))

    stats = DedupeStats(
        input_count=count,
        output_count=len(result),
        merged_groups=merged_groups,
        skipped_rows=skipped,
    )
    return result, stats


def dedupe_csv_file(
    input_path: Path,
    output_path: Path,
    cfg: Optional[DedupeConfig] = None,
) -> DedupeStats:
    """Read a Proton Pass CSV file, deduplicate entries, and write the result."""
    from .model import VaultItem
    from .plugins.protonpass_plugin import register_protonpass_plugin
    from .plugins.provider_types import ProviderFormat
    from .plugins.registry import get_registry
    from .protonpass import dedupe_proton_vault_items

    # Ensure the Proton Pass plugin is registered so we can resolve it from the
    # registry even if callers import :mod:`cred_dedupe.core` directly.
    register_protonpass_plugin()

    registry = get_registry()
    proton_plugin = registry.get(ProviderFormat.PROTONPASS)
    if cfg is None:
        cfg = DedupeConfig()

    input_path = input_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()

    items: List[VaultItem] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing_cols = [c for c in CSV_INPUT_COLUMNS if c not in reader.fieldnames]
        if missing_cols:
            raise ValueError(
                f"Input CSV is missing columns: {', '.join(missing_cols)}"
            )

        for row in reader:
            items.append(proton_plugin.import_row(row))

    deduped_items, stats = dedupe_proton_vault_items(items, cfg)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_OUTPUT_COLUMNS)
        writer.writeheader()
        for item in deduped_items:
            writer.writerow(proton_plugin.export_row(item))

    return stats


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Credential deduplication tool with a simple Qt6 GUI for cleaning password-manager CSV exports.",
        epilog=(
            "DISCLAIMER: This project and its author are not affiliated with, "
            "endorsed by, or sponsored by any password application."
        ),
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input credential CSV file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output CSV file. Default: <input>_deduped.csv",
    )
    parser.add_argument(
        "--allow-different-passwords",
        action="store_true",
        help=(
            "Allow merging entries even when passwords differ. "
            "This is more aggressive and may merge unrelated entries, "
            "but can help consolidate accounts where the password has "
            "changed over time."
        ),
    )
    parser.add_argument(
        "--no-email-username-equivalence",
        action="store_true",
        help=(
            "Do not treat email and username as equivalent login identifiers. "
            "By default they are treated as interchangeable."
        ),
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.is_file():
        parser.error(f"Input file not found: {input_path}")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(
            input_path.stem + "_deduped" + input_path.suffix
        )

    cfg = DedupeConfig(
        strict_password_match=not args.allow_different_passwords,
        treat_email_username_equivalent=not args.no_email_username_equivalence,
    )

    stats = dedupe_csv_file(input_path, output_path, cfg)

    print(
        f"Processed {stats.input_count} rows -> {stats.output_count} rows "
        f"({stats.merged_groups} groups merged, {stats.skipped_rows} ungrouped)."
    )
    print(f"Output written to: {output_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())

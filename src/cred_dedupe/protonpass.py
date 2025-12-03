from __future__ import annotations

"""Proton Pass CSV <-> VaultItem adapter layer.

This module is responsible for translating between Proton Pass CSV rows and the
canonical :class:`VaultItem` model used internally for deduplication.

Current Proton Pass CSV columns expected on import:

- ``type``: item type string (e.g. ``"login"``).
- ``name``: item name.
- ``url``: login URL.
- ``email``: email address field (treated as an alternative username).
- ``username``: primary username.
- ``password``: password.
- ``note``: free-form notes.
- ``totp``: TOTP secret or otpauth:// URI.
- ``createTime``: creation timestamp (provider-specific format).
- ``modifyTime``: modification timestamp (provider-specific format).
- ``vault``: vault/container name.

When exporting to Proton Pass CSV we currently emit the following columns
(matching ``CSV_OUTPUT_COLUMNS`` in :mod:`cred_dedupe.core`):

- ``name``, ``url``, ``email``, ``username``, ``password``, ``note``, ``totp``, ``vault``.

Provider-specific details such as the original timestamps or item type are
stored in :attr:`VaultItem.extra` using Proton-prefixed keys so that they can
be preserved across round-trips even if they are not directly used for
deduplication.
"""

from typing import Dict, Iterable, List, Optional, Tuple

from .core import (
    DedupeConfig,
    DedupeStats,
    Entry,
    _normalize_domain,
    _normalize_login,
    dedupe_entries,
)
from .model import ItemType, VaultItem
from .utils import normalize_url


_PROTON_TYPE_TO_ITEM_TYPE: Dict[str, ItemType] = {
    "login": ItemType.LOGIN,
    "note": ItemType.NOTE,
    "card": ItemType.CARD,
    "identity": ItemType.IDENTITY,
}


def _map_proton_type(raw_type: str) -> ItemType:
    key = (raw_type or "").strip().lower()
    return _PROTON_TYPE_TO_ITEM_TYPE.get(key, ItemType.OTHER)


def proton_row_to_vault_item(row: Dict[str, str]) -> VaultItem:
    """Map a single Proton Pass CSV row to a :class:`VaultItem`."""
    type_raw = row.get("type", "") or ""
    name = row.get("name", "") or ""
    url = row.get("url", "") or ""
    email = row.get("email", "") or ""
    username = row.get("username", "") or ""
    password = row.get("password", "") or ""
    note = row.get("note", "") or ""
    totp_raw = row.get("totp", "") or ""
    create_time = row.get("createTime", "") or ""
    modify_time = row.get("modifyTime", "") or ""
    vault = row.get("vault", "") or ""

    primary_url = normalize_url(url) if url else None

    totp_uri: Optional[str]
    totp_secret: Optional[str]
    if totp_raw.startswith("otpauth://"):
        totp_uri = totp_raw
        totp_secret = None
    else:
        totp_uri = None
        totp_secret = totp_raw or None

    extra = {
        "proton_type": type_raw,
        "proton_email": email,
        "proton_createTime": create_time,
        "proton_modifyTime": modify_time,
        "proton_vault": vault,
        "proton_raw_url": url,
        "proton_totp": totp_raw,
    }

    return VaultItem(
        item_type=_map_proton_type(type_raw),
        source="protonpass",
        title=name,
        username=username,
        password=password,
        primary_url=primary_url,
        notes=note,
        totp_uri=totp_uri,
        totp_secret=totp_secret,
        extra=extra,
    )


def _vault_item_to_entry(item: VaultItem, cfg: DedupeConfig) -> Entry:
    """Convert a :class:`VaultItem` (assumed to originate from Proton) into Entry."""
    type_raw = item.extra.get("proton_type", "") or ""
    raw_url = item.extra.get("proton_raw_url") or (item.primary_url or "")
    email = item.extra.get("proton_email", "") or ""
    totp_raw = item.extra.get("proton_totp", "") or ""
    create_time = item.extra.get("proton_createTime", "") or ""
    modify_time = item.extra.get("proton_modifyTime", "") or ""
    vault = item.extra.get("proton_vault", "") or ""

    entry = Entry(
        type=type_raw,
        name=item.title,
        url=raw_url,
        email=email,
        username=item.username,
        password=item.password,
        note=item.notes,
        totp=totp_raw,
        createTime=create_time,
        modifyTime=modify_time,
        vault=vault,
    )
    entry.canonical_domain = _normalize_domain(entry.url)
    entry.login_id = _normalize_login(entry, cfg)
    return entry


def _entry_to_vault_item(entry: Entry) -> VaultItem:
    """Convert a Proton :class:`Entry` into a :class:`VaultItem`."""
    type_raw = entry.type or ""
    item_type = _map_proton_type(type_raw)

    url = entry.url or ""
    primary_url = normalize_url(url) if url else None

    totp_raw = entry.totp or ""
    if totp_raw.startswith("otpauth://"):
        totp_uri = totp_raw
        totp_secret = None
    else:
        totp_uri = None
        totp_secret = totp_raw or None

    extra = {
        "proton_type": type_raw,
        "proton_email": entry.email or "",
        "proton_createTime": entry.createTime or "",
        "proton_modifyTime": entry.modifyTime or "",
        "proton_vault": entry.vault or "",
        "proton_raw_url": url,
        "proton_totp": totp_raw,
    }

    return VaultItem(
        item_type=item_type,
        source="protonpass",
        title=entry.name or "",
        username=entry.username or "",
        password=entry.password or "",
        primary_url=primary_url,
        notes=entry.note or "",
        totp_uri=totp_uri,
        totp_secret=totp_secret,
        extra=extra,
    )


def dedupe_proton_vault_items(
    items: Iterable[VaultItem],
    cfg: Optional[DedupeConfig] = None,
) -> Tuple[List[VaultItem], DedupeStats]:
    """Deduplicate a sequence of Proton-origin :class:`VaultItem` objects.

    This function preserves the existing Proton-specific deduplication behavior
    by converting :class:`VaultItem` instances into the legacy :class:`Entry`
    objects, running :func:`dedupe_entries`, and then mapping the merged
    entries back into :class:`VaultItem` objects.
    """
    if cfg is None:
        cfg = DedupeConfig()

    entries = [_vault_item_to_entry(item, cfg) for item in items]
    deduped_entries, stats = dedupe_entries(entries, cfg)
    deduped_items = [_entry_to_vault_item(e) for e in deduped_entries]
    return deduped_items, stats


def vault_item_to_proton_row(item: VaultItem) -> Dict[str, str]:
    """Map a :class:`VaultItem` back into a Proton Pass CSV row dict."""
    # Prefer the original Proton URL when available so that we preserve the
    # exact string the user exported (including scheme or minor quirks).
    raw_url = item.extra.get("proton_raw_url") or (item.primary_url or "")

    email = item.extra.get("proton_email", "") or ""
    vault = item.extra.get("proton_vault", "") or ""

    # Prefer the original Proton TOTP string if we have it; otherwise rebuild
    # from the canonical fields.
    totp_raw = item.extra.get("proton_totp", "") or ""
    if not totp_raw:
        if item.totp_uri:
            totp_raw = item.totp_uri
        elif item.totp_secret:
            totp_raw = item.totp_secret

    return {
        "name": item.title,
        "url": raw_url,
        "email": email,
        "username": item.username,
        "password": item.password,
        "note": item.notes,
        "totp": totp_raw,
        "vault": vault,
    }


__all__ = [
    "proton_row_to_vault_item",
    "vault_item_to_proton_row",
    "dedupe_proton_vault_items",
]

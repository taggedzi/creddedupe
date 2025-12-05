# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ItemType(str, Enum):
    """Canonical item type for all vault items."""

    LOGIN = "login"
    NOTE = "note"
    CARD = "card"
    IDENTITY = "identity"
    OTHER = "other"


@dataclass
class VaultItem:
    """Canonical internal representation of a credential or vault item.

    This model is provider-agnostic and is intended as the common shape used
    throughout the deduplication pipeline. Provider-specific adapters
    (e.g. Proton Pass CSV) are responsible for mapping into and out of this
    structure.
    """

    # Identity / provenance
    item_type: ItemType = ItemType.LOGIN
    internal_id: Optional[str] = None  # our own UUID or similar
    source: Optional[str] = None  # "protonpass", "lastpass", "bitwarden", etc.
    source_id: Optional[str] = None  # provider GUID / id if available

    # Core login fields
    title: str = ""
    username: str = ""
    password: str = ""

    # URL / site info
    primary_url: Optional[str] = None
    secondary_urls: List[str] = field(default_factory=list)

    # Human notes / description
    notes: str = ""

    # Organization / flags
    folder: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    favorite: bool = False

    # OTP / 2FA
    totp_uri: Optional[str] = None  # full otpauth:// URI if available
    totp_secret: Optional[str] = None  # raw shared secret if that’s all we have

    # Timestamps (epoch ms; internal convention = UTC)
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    # Catch-all for provider-specific data
    extra: Dict[str, str] = field(default_factory=dict)

    def __hash__(self) -> int:
        # Use object identity for hashing so VaultItem instances can be placed
        # in sets or used as dict keys without relying on mutable field values.
        return id(self)


__all__ = ["ItemType", "VaultItem"]


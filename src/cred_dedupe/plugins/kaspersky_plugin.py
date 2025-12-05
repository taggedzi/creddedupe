# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Dict

from ..model import ItemType, VaultItem
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class KasperskyPlugin(BaseProviderPlugin):
    """Provider plugin for Kaspersky CSV import format."""

    provider_type = ProviderFormat.KASPERSKY
    header_spec = HeaderSpec(
        required={"Account", "Login", "Password", "Url"},
        optional=set(),
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        title = row.get("Account", "") or ""
        username = row.get("Login", "") or ""
        password = row.get("Password", "") or ""
        primary_url = row.get("Url") or None

        return VaultItem(
            item_type=ItemType.LOGIN,
            source="kaspersky",
            title=title,
            username=username,
            password=password,
            primary_url=primary_url,
        )

    def export_row(self, item: VaultItem) -> Dict[str, str]:
        return {
            "Account": item.title or (item.primary_url or ""),
            "Login": item.username,
            "Password": item.password,
            "Url": item.primary_url or "",
        }


def register_kaspersky_plugin() -> None:
    registry = get_registry()
    try:
        registry.register(KasperskyPlugin())
    except ValueError:
        pass


__all__ = ["KasperskyPlugin", "register_kaspersky_plugin"]


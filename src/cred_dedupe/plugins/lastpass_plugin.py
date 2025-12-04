from __future__ import annotations

from typing import Dict

from ..model import ItemType, VaultItem
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class LastPassPlugin(BaseProviderPlugin):
    """Provider plugin for LastPass CSV format."""

    provider_type = ProviderFormat.LASTPASS
    header_spec = HeaderSpec(
        required={"url", "username", "password"},
        optional={"totp", "extra", "name", "grouping", "fav"},
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        title = row.get("name", "") or ""
        username = row.get("username", "") or ""
        password = row.get("password", "") or ""
        primary_url = row.get("url") or None
        notes = row.get("extra", "") or ""
        folder = row.get("grouping") or None
        favorite = (row.get("fav") or "") == "1"
        totp_secret = row.get("totp") or None

        extra: Dict[str, str] = {}
        for key, value in row.items():
            if key not in {
                "url",
                "username",
                "password",
                "totp",
                "extra",
                "name",
                "grouping",
                "fav",
            }:
                extra[key] = value

        return VaultItem(
            item_type=ItemType.LOGIN,
            source="lastpass",
            title=title,
            username=username,
            password=password,
            primary_url=primary_url,
            notes=notes,
            folder=folder,
            favorite=favorite,
            totp_secret=totp_secret,
            extra=extra,
        )

    def export_row(self, item: VaultItem) -> Dict[str, str]:
        return {
            "url": item.primary_url or "",
            "username": item.username,
            "password": item.password,
            "totp": item.totp_secret or "",
            "extra": item.notes or "",
            "name": item.title or (item.primary_url or ""),
            "grouping": item.folder or "",
            "fav": "1" if item.favorite else "0",
        }


def register_lastpass_plugin() -> None:
    registry = get_registry()
    try:
        registry.register(LastPassPlugin())
    except ValueError:
        pass


__all__ = ["LastPassPlugin", "register_lastpass_plugin"]


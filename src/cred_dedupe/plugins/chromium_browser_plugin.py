from __future__ import annotations

from typing import Dict

from ..model import ItemType, VaultItem
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class ChromiumBrowserPlugin(BaseProviderPlugin):
    """Provider plugin for Chromium-based browser CSV formats."""

    provider_type = ProviderFormat.CHROMIUM_BROWSER
    header_spec = HeaderSpec(
        required={"name", "url", "username", "password"},
        optional={"note"},
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        title = row.get("name", "") or ""
        primary_url = row.get("url") or None
        username = row.get("username", "") or ""
        password = row.get("password", "") or ""
        notes = row.get("note", "") or ""

        return VaultItem(
            item_type=ItemType.LOGIN,
            source="chromium_browser",
            title=title,
            username=username,
            password=password,
            primary_url=primary_url,
            notes=notes,
        )

    def export_row(self, item: VaultItem) -> Dict[str, str]:
        return {
            "name": item.title or (item.primary_url or ""),
            "url": item.primary_url or "",
            "username": item.username,
            "password": item.password,
            "note": item.notes or "",
        }


def register_chromium_browser_plugin() -> None:
    registry = get_registry()
    try:
        registry.register(ChromiumBrowserPlugin())
    except ValueError:
        pass


__all__ = ["ChromiumBrowserPlugin", "register_chromium_browser_plugin"]


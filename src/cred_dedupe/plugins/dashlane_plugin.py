from __future__ import annotations

from typing import Dict

from ..model import ItemType, VaultItem
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class DashlanePlugin(BaseProviderPlugin):
    """Provider plugin for Dashlane CSV template."""

    provider_type = ProviderFormat.DASHLANE
    header_spec = HeaderSpec(
        required={"Type", "Name", "Website URL", "Password"},
        optional={"Username", "Email", "Secondary Login", "Comment", "collections"},
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        raw_type = (row.get("Type") or "").strip().lower()
        # For now we only handle logins explicitly; other types become OTHER.
        if raw_type.startswith("login"):
            item_type = ItemType.LOGIN
        else:
            item_type = ItemType.OTHER

        title = row.get("Name", "") or ""
        primary_url = row.get("Website URL") or None

        username = row.get("Username", "") or ""
        if not username:
            username = row.get("Email", "") or ""

        password = row.get("Password", "") or ""
        notes = row.get("Comment", "") or ""

        extra: Dict[str, str] = {}
        for key, value in row.items():
            if key not in {
                "Type",
                "Name",
                "Website URL",
                "Username",
                "Email",
                "Secondary Login",
                "Password",
                "Comment",
                "collections",
            }:
                extra[key] = value

        if "Secondary Login" in row:
            extra["Secondary Login"] = row.get("Secondary Login", "") or ""
        if "collections" in row:
            extra["collections"] = row.get("collections", "") or ""

        return VaultItem(
            item_type=item_type,
            source="dashlane",
            title=title,
            username=username,
            password=password,
            primary_url=primary_url,
            notes=notes,
            extra=extra,
        )

    def export_row(self, item: VaultItem) -> Dict[str, str]:
        return {
            "Type": "Login",
            "Name": item.title or (item.primary_url or ""),
            "Website URL": item.primary_url or "",
            "Username": item.username,
            "Email": "",
            "Secondary Login": "",
            "Password": item.password,
            "Comment": item.notes or "",
            "collections": "",
        }


def register_dashlane_plugin() -> None:
    registry = get_registry()
    try:
        registry.register(DashlanePlugin())
    except ValueError:
        pass


__all__ = ["DashlanePlugin", "register_dashlane_plugin"]


from __future__ import annotations

from typing import Dict

from ..model import ItemType, VaultItem
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class ApplePasswordsPlugin(BaseProviderPlugin):
    """Provider plugin for Apple Passwords / Safari CSV format."""

    provider_type = ProviderFormat.APPLE_PASSWORDS
    header_spec = HeaderSpec(
        required={"Title", "URL", "Username", "Password"},
        optional={"Notes", "OTPAuth"},
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        title = row.get("Title", "") or ""
        primary_url = row.get("URL") or None
        username = row.get("Username", "") or ""
        password = row.get("Password", "") or ""
        notes = row.get("Notes", "") or ""
        totp_uri = row.get("OTPAuth") or None

        return VaultItem(
            item_type=ItemType.LOGIN,
            source="apple_passwords",
            title=title,
            username=username,
            password=password,
            primary_url=primary_url,
            notes=notes,
            totp_uri=totp_uri,
        )

    def export_row(self, item: VaultItem) -> Dict[str, str]:
        return {
            "Title": item.title or (item.primary_url or ""),
            "URL": item.primary_url or "",
            "Username": item.username,
            "Password": item.password,
            "Notes": item.notes or "",
            "OTPAuth": item.totp_uri or "",
        }


def register_apple_passwords_plugin() -> None:
    registry = get_registry()
    try:
        registry.register(ApplePasswordsPlugin())
    except ValueError:
        pass


__all__ = ["ApplePasswordsPlugin", "register_apple_passwords_plugin"]


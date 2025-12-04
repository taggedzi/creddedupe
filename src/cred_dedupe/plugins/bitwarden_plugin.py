from __future__ import annotations

from typing import Dict

from ..model import ItemType, VaultItem
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class BitwardenPlugin(BaseProviderPlugin):
    """Provider plugin for Bitwarden individual vault CSV format."""

    provider_type = ProviderFormat.BITWARDEN
    header_spec = HeaderSpec(
        required={"type", "name"},
        optional={
            "folder",
            "favorite",
            "notes",
            "fields",
            "reprompt",
            "login_uri",
            "login_username",
            "login_password",
            "login_totp",
        },
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        raw_type = (row.get("type") or "").strip().lower()
        if raw_type == "note":
            item_type = ItemType.NOTE
        else:
            item_type = ItemType.LOGIN

        title = row.get("name", "") or ""
        username = row.get("login_username", "") or ""
        password = row.get("login_password", "") or ""
        primary_url = row.get("login_uri") or None
        notes = row.get("notes", "") or ""
        folder = row.get("folder") or None
        favorite = (row.get("favorite") or "") == "1"
        totp_secret = row.get("login_totp") or None

        extra: Dict[str, str] = {}
        for key, value in row.items():
            if key not in {
                "folder",
                "favorite",
                "type",
                "name",
                "notes",
                "fields",
                "reprompt",
                "login_uri",
                "login_username",
                "login_password",
                "login_totp",
            }:
                extra[key] = value

        # Preserve specific known fields in extra for round-tripping.
        for key in ("fields", "reprompt"):
            if key in row:
                extra[key] = row.get(key, "") or ""

        return VaultItem(
            item_type=item_type,
            source="bitwarden",
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
        if item.item_type is ItemType.NOTE:
            item_type = "note"
        else:
            item_type = "login"

        fields = item.extra.get("fields", "")
        reprompt = item.extra.get("reprompt", "")

        return {
            "folder": item.folder or "",
            "favorite": "1" if item.favorite else "0",
            "type": item_type,
            "name": item.title,
            "notes": item.notes or "",
            "fields": fields,
            "reprompt": reprompt,
            "login_uri": item.primary_url or "",
            "login_username": item.username,
            "login_password": item.password,
            "login_totp": item.totp_secret or "",
        }


def register_bitwarden_plugin() -> None:
    registry = get_registry()
    try:
        registry.register(BitwardenPlugin())
    except ValueError:
        pass


__all__ = ["BitwardenPlugin", "register_bitwarden_plugin"]


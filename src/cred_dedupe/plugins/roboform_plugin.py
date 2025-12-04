from __future__ import annotations

from typing import Dict

from ..model import ItemType, VaultItem
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class RoboFormPlugin(BaseProviderPlugin):
    """Provider plugin for RoboForm CSV formats."""

    provider_type = ProviderFormat.ROBOFORM
    header_spec = HeaderSpec(
        required={"Name", "URL", "Login", "Password"},
        optional={"MatchUrl", "Note", "Folder", "RfFieldsV2", "Pwd"},
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        title = row.get("Name", "") or ""
        primary_url = row.get("URL") or None
        username = row.get("Login", "") or ""
        password = row.get("Password", "") or row.get("Pwd", "") or ""
        notes = row.get("Note", "") or ""
        folder = row.get("Folder") or None

        extra: Dict[str, str] = {}
        for key in ("MatchUrl", "RfFieldsV2"):
            if key in row:
                extra[key] = row.get(key, "") or ""
        for key, value in row.items():
            if key not in {
                "Name",
                "URL",
                "Login",
                "Password",
                "Pwd",
                "Note",
                "Folder",
                "MatchUrl",
                "RfFieldsV2",
            }:
                extra[key] = value

        return VaultItem(
            item_type=ItemType.LOGIN,
            source="roboform",
            title=title,
            username=username,
            password=password,
            primary_url=primary_url,
            notes=notes,
            folder=folder,
            extra=extra,
        )

    def export_row(self, item: VaultItem) -> Dict[str, str]:
        return {
            "Name": item.title or (item.primary_url or ""),
            "URL": item.primary_url or "",
            "Login": item.username,
            "Pwd": item.password,
            "Note": item.notes or "",
            "Folder": item.folder or "",
        }


def register_roboform_plugin() -> None:
    registry = get_registry()
    try:
        registry.register(RoboFormPlugin())
    except ValueError:
        pass


__all__ = ["RoboFormPlugin", "register_roboform_plugin"]


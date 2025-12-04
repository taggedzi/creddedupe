from __future__ import annotations

from typing import Dict

from ..model import ItemType, VaultItem
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class NordPassPlugin(BaseProviderPlugin):
    """Provider plugin for NordPass CSV template."""

    provider_type = ProviderFormat.NORDPASS
    header_spec = HeaderSpec(
        required={"name", "url", "username", "password"},
        optional={
            "note",
            "cardholdername",
            "cardnumber",
            "cvc",
            "expirydate",
            "zipcode",
            "folder",
            "full_name",
            "phone_number",
            "email",
            "address1",
            "address2",
            "city",
            "country",
            "state",
        },
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        title = row.get("name", "") or ""
        primary_url = row.get("url") or None
        username = row.get("username", "") or ""
        password = row.get("password", "") or ""
        notes = row.get("note", "") or ""
        folder = row.get("folder") or None

        # Infer item type based on presence of card/identity fields.
        if any(row.get(k, "").strip() for k in ("cardnumber", "cardholdername")):
            item_type = ItemType.CARD
        elif any(row.get(k, "").strip() for k in ("full_name", "address1", "city")):
            item_type = ItemType.IDENTITY
        else:
            item_type = ItemType.LOGIN

        extra: Dict[str, str] = {}
        for key, value in row.items():
            if key not in {
                "name",
                "url",
                "username",
                "password",
                "note",
                "folder",
            }:
                extra[key] = value

        return VaultItem(
            item_type=item_type,
            source="nordpass",
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
            "name": item.title,
            "url": item.primary_url or "",
            "username": item.username,
            "password": item.password,
            "note": item.notes or "",
            "cardholdername": item.extra.get("cardholdername", ""),
            "cardnumber": item.extra.get("cardnumber", ""),
            "cvc": item.extra.get("cvc", ""),
            "expirydate": item.extra.get("expirydate", ""),
            "zipcode": item.extra.get("zipcode", ""),
            "folder": item.folder or "",
            "full_name": item.extra.get("full_name", ""),
            "phone_number": item.extra.get("phone_number", ""),
            "email": item.extra.get("email", ""),
            "address1": item.extra.get("address1", ""),
            "address2": item.extra.get("address2", ""),
            "city": item.extra.get("city", ""),
            "country": item.extra.get("country", ""),
            "state": item.extra.get("state", ""),
        }


def register_nordpass_plugin() -> None:
    registry = get_registry()
    try:
        registry.register(NordPassPlugin())
    except ValueError:
        pass


__all__ = ["NordPassPlugin", "register_nordpass_plugin"]


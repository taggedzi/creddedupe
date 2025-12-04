from __future__ import annotations

from typing import Dict

from ..model import ItemType, VaultItem
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class FirefoxPlugin(BaseProviderPlugin):
    """Provider plugin for Firefox about:logins CSV format."""

    provider_type = ProviderFormat.FIREFOX
    header_spec = HeaderSpec(
        required={"url", "username", "password"},
        optional={
            "httpRealm",
            "formActionOrigin",
            "guid",
            "timeCreated",
            "timeLastUsed",
            "timePasswordChanged",
        },
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        primary_url = row.get("url") or None
        username = row.get("username", "") or ""
        password = row.get("password", "") or ""

        guid = row.get("guid") or None

        def _parse_int(value: str | None) -> int | None:
            if not value:
                return None
            try:
                return int(value)
            except ValueError:
                return None

        created_at = _parse_int(row.get("timeCreated"))
        updated_at = _parse_int(row.get("timePasswordChanged") or row.get("timeLastUsed"))

        extra: Dict[str, str] = {}
        for key in ("httpRealm", "formActionOrigin", "timeLastUsed"):
            if key in row:
                extra[key] = row.get(key, "") or ""

        return VaultItem(
            item_type=ItemType.LOGIN,
            source="firefox",
            source_id=guid,
            title="",
            username=username,
            password=password,
            primary_url=primary_url,
            created_at=created_at,
            updated_at=updated_at,
            extra=extra,
        )

    def export_row(self, item: VaultItem) -> Dict[str, str]:
        http_realm = item.extra.get("httpRealm", "")
        form_action_origin = item.extra.get("formActionOrigin", "")
        time_last_used = item.extra.get("timeLastUsed", "")

        created_at = str(item.created_at or 0)
        updated_at = str(item.updated_at or 0)

        return {
            "url": item.primary_url or "",
            "username": item.username,
            "password": item.password,
            "httpRealm": http_realm,
            "formActionOrigin": form_action_origin,
            "guid": item.source_id or "",
            "timeCreated": created_at,
            "timeLastUsed": time_last_used or "0",
            "timePasswordChanged": updated_at,
        }


def register_firefox_plugin() -> None:
    registry = get_registry()
    try:
        registry.register(FirefoxPlugin())
    except ValueError:
        pass


__all__ = ["FirefoxPlugin", "register_firefox_plugin"]


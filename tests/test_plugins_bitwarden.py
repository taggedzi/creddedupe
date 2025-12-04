from __future__ import annotations

from typing import Dict

from cred_dedupe.model import ItemType, VaultItem
from cred_dedupe.plugins.bitwarden_plugin import (
    BitwardenPlugin,
    register_bitwarden_plugin,
)
from cred_dedupe.plugins.provider_types import ProviderFormat
from cred_dedupe.plugins.registry import get_registry


def _make_bitwarden_login_row() -> Dict[str, str]:
    return {
        "folder": "Personal",
        "favorite": "1",
        "type": "login",
        "name": "Example",
        "notes": "bitwarden note",
        "fields": "",
        "reprompt": "0",
        "login_uri": "https://example.com/login",
        "login_username": "user",
        "login_password": "secret",
        "login_totp": "ABC",
    }


def test_bitwarden_plugin_registration() -> None:
    register_bitwarden_plugin()
    registry = get_registry()

    plugin = registry.get(ProviderFormat.BITWARDEN)
    assert isinstance(plugin, BitwardenPlugin)
    assert plugin.provider_type is ProviderFormat.BITWARDEN


def test_bitwarden_import_export_mapping_login() -> None:
    plugin = BitwardenPlugin()
    row = _make_bitwarden_login_row()

    item = plugin.import_row(row)
    assert isinstance(item, VaultItem)
    assert item.source == "bitwarden"
    assert item.item_type is ItemType.LOGIN
    assert item.title == "Example"
    assert item.username == "user"
    assert item.password == "secret"
    assert item.primary_url == "https://example.com/login"
    assert item.notes == "bitwarden note"
    assert item.folder == "Personal"
    assert item.favorite is True
    assert item.totp_secret == "ABC"

    exported = plugin.export_row(item)
    assert exported["type"] == "login"
    assert exported["name"] == "Example"
    assert exported["login_username"] == "user"
    assert exported["login_password"] == "secret"
    assert exported["login_uri"] == "https://example.com/login"
    assert exported["favorite"] == "1"
    assert exported["folder"] == "Personal"


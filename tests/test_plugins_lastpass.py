from __future__ import annotations

from typing import Dict

from cred_dedupe.model import VaultItem
from cred_dedupe.plugins.lastpass_plugin import (
    LastPassPlugin,
    register_lastpass_plugin,
)
from cred_dedupe.plugins.provider_types import ProviderFormat
from cred_dedupe.plugins.registry import get_registry


def _make_lastpass_row() -> Dict[str, str]:
    return {
        "url": "https://example.com/login",
        "username": "user",
        "password": "secret",
        "totp": "ABCDEF",
        "extra": "some note",
        "name": "Example",
        "grouping": "Personal",
        "fav": "1",
    }


def test_lastpass_plugin_registration() -> None:
    register_lastpass_plugin()
    registry = get_registry()

    plugin = registry.get(ProviderFormat.LASTPASS)
    assert isinstance(plugin, LastPassPlugin)
    assert plugin.provider_type is ProviderFormat.LASTPASS


def test_lastpass_import_export_mapping() -> None:
    plugin = LastPassPlugin()
    row = _make_lastpass_row()

    item = plugin.import_row(row)
    assert isinstance(item, VaultItem)
    assert item.source == "lastpass"
    assert item.title == "Example"
    assert item.username == "user"
    assert item.password == "secret"
    assert item.primary_url == "https://example.com/login"
    assert item.notes == "some note"
    assert item.folder == "Personal"
    assert item.favorite is True
    assert item.totp_secret == "ABCDEF"

    exported = plugin.export_row(item)
    assert list(exported.keys()) == [
        "url",
        "username",
        "password",
        "totp",
        "extra",
        "name",
        "grouping",
        "fav",
    ]
    assert exported["url"] == row["url"]
    assert exported["username"] == row["username"]
    assert exported["password"] == row["password"]
    assert exported["extra"] == row["extra"]
    assert exported["name"] == row["name"]
    assert exported["grouping"] == row["grouping"]
    assert exported["fav"] == "1"


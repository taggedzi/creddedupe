# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Dict

from cred_dedupe.core import CSV_INPUT_COLUMNS, CSV_OUTPUT_COLUMNS
from cred_dedupe.model import VaultItem
from cred_dedupe.plugins.provider_types import ProviderFormat
from cred_dedupe.plugins.registry import get_registry
from cred_dedupe.plugins.protonpass_plugin import (
    ProtonPassPlugin,
    register_protonpass_plugin,
)


def _make_sample_proton_row() -> Dict[str, str]:
    return {
        "type": "login",
        "name": "Example",
        "url": "https://Example.com/login/",
        "email": "user@example.com",
        "username": "user",
        "password": "secret",
        "note": "some note",
        "totp": "otpauth://totp/Example?secret=ABC",
        "createTime": "1",
        "modifyTime": "10",
        "vault": "Default",
    }


def test_protonpass_plugin_registration() -> None:
    register_protonpass_plugin()
    registry = get_registry()

    plugin = registry.get(ProviderFormat.PROTONPASS)
    assert isinstance(plugin, ProtonPassPlugin)
    assert plugin.provider_type is ProviderFormat.PROTONPASS


def test_protonpass_import_export_roundtrip_simple() -> None:
    register_protonpass_plugin()
    registry = get_registry()
    plugin = registry.get(ProviderFormat.PROTONPASS)

    row = _make_sample_proton_row()
    item = plugin.import_row(row)

    assert isinstance(item, VaultItem)
    assert item.title == row["name"]
    assert item.username == row["username"]
    assert item.password == row["password"]
    assert item.source == "protonpass"
    # URL should be normalized but still point to the same host/path.
    assert item.primary_url == "https://example.com/login"

    exported = plugin.export_row(item)

    # Ensure all expected output columns are present.
    for col in CSV_OUTPUT_COLUMNS:
        assert col in exported

    # Values that should survive a simple round-trip unchanged.
    assert exported["name"] == row["name"]
    assert exported["url"] == row["url"]
    assert exported["username"] == row["username"]
    assert exported["password"] == row["password"]
    assert exported["note"] == row["note"]
    assert exported["totp"] == row["totp"]
    assert exported["vault"] == row["vault"]


def test_protonpass_header_spec_normalization() -> None:
    register_protonpass_plugin()
    registry = get_registry()
    plugin = registry.get(ProviderFormat.PROTONPASS)

    # Required headers should match the CSV_INPUT_COLUMNS set.
    assert plugin.header_spec.required == set(CSV_INPUT_COLUMNS)
    assert plugin.header_spec.optional == set()

    normalized = plugin.normalized_required_headers()
    expected_normalized = {h.lower() for h in CSV_INPUT_COLUMNS}
    assert normalized == expected_normalized


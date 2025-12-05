# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Dict

from cred_dedupe.model import ItemType
from cred_dedupe.plugins.apple_passwords_plugin import (
    ApplePasswordsPlugin,
    register_apple_passwords_plugin,
)
from cred_dedupe.plugins.chromium_browser_plugin import (
    ChromiumBrowserPlugin,
    register_chromium_browser_plugin,
)
from cred_dedupe.plugins.dashlane_plugin import (
    DashlanePlugin,
    register_dashlane_plugin,
)
from cred_dedupe.plugins.firefox_plugin import (
    FirefoxPlugin,
    register_firefox_plugin,
)
from cred_dedupe.plugins.kaspersky_plugin import (
    KasperskyPlugin,
    register_kaspersky_plugin,
)
from cred_dedupe.plugins.nordpass_plugin import (
    NordPassPlugin,
    register_nordpass_plugin,
)
from cred_dedupe.plugins.provider_types import ProviderFormat
from cred_dedupe.plugins.registry import get_registry
from cred_dedupe.plugins.roboform_plugin import (
    RoboFormPlugin,
    register_roboform_plugin,
)


def test_dashlane_plugin_basic_mapping() -> None:
    register_dashlane_plugin()
    registry = get_registry()
    plugin = registry.get(ProviderFormat.DASHLANE)
    assert isinstance(plugin, DashlanePlugin)

    row: Dict[str, str] = {
        "Type": "Login",
        "Name": "Example",
        "Website URL": "https://example.com/login",
        "Username": "user",
        "Email": "",
        "Secondary Login": "",
        "Password": "secret",
        "Comment": "dashlane note",
        "collections": "",
    }

    item = plugin.import_row(row)
    assert item.source == "dashlane"
    assert item.item_type is ItemType.LOGIN
    assert item.title == "Example"
    assert item.username == "user"
    assert item.password == "secret"
    assert item.primary_url == "https://example.com/login"
    assert item.notes == "dashlane note"

    exported = plugin.export_row(item)
    assert exported["Type"] == "Login"
    assert exported["Name"] == "Example"
    assert exported["Website URL"] == "https://example.com/login"


def test_roboform_plugin_basic_mapping() -> None:
    register_roboform_plugin()
    registry = get_registry()
    plugin = registry.get(ProviderFormat.ROBOFORM)
    assert isinstance(plugin, RoboFormPlugin)

    row: Dict[str, str] = {
        "Name": "Example",
        "URL": "https://example.com/login",
        "Login": "user",
        "Password": "secret",
        "Note": "robo note",
        "Folder": "Personal",
        "MatchUrl": "https://example.com/login",
        "RfFieldsV2": "metadata",
    }

    item = plugin.import_row(row)
    assert item.source == "roboform"
    assert item.title == "Example"
    assert item.username == "user"
    assert item.password == "secret"
    assert item.primary_url == "https://example.com/login"
    assert item.notes == "robo note"
    assert item.folder == "Personal"
    assert item.extra.get("MatchUrl") == "https://example.com/login"
    assert item.extra.get("RfFieldsV2") == "metadata"

    exported = plugin.export_row(item)
    assert exported["Name"] == "Example"
    assert exported["URL"] == "https://example.com/login"
    assert exported["Login"] == "user"
    assert exported["Pwd"] == "secret"


def test_nordpass_plugin_basic_mapping() -> None:
    register_nordpass_plugin()
    registry = get_registry()
    plugin = registry.get(ProviderFormat.NORDPASS)
    assert isinstance(plugin, NordPassPlugin)

    row: Dict[str, str] = {
        "name": "Example",
        "url": "https://example.com/login",
        "username": "user",
        "password": "secret",
        "note": "nord note",
        "folder": "Personal",
        "cardholdername": "",
        "cardnumber": "",
        "cvc": "",
        "expirydate": "",
        "zipcode": "",
        "full_name": "",
        "phone_number": "",
        "email": "",
        "address1": "",
        "address2": "",
        "city": "",
        "country": "",
        "state": "",
    }

    item = plugin.import_row(row)
    assert item.source == "nordpass"
    assert item.item_type is ItemType.LOGIN
    assert item.title == "Example"
    assert item.username == "user"
    assert item.password == "secret"
    assert item.primary_url == "https://example.com/login"
    assert item.notes == "nord note"
    assert item.folder == "Personal"

    exported = plugin.export_row(item)
    assert exported["name"] == "Example"
    assert exported["url"] == "https://example.com/login"
    assert exported["username"] == "user"
    assert exported["password"] == "secret"


def test_apple_passwords_plugin_basic_mapping() -> None:
    register_apple_passwords_plugin()
    registry = get_registry()
    plugin = registry.get(ProviderFormat.APPLE_PASSWORDS)
    assert isinstance(plugin, ApplePasswordsPlugin)

    row: Dict[str, str] = {
        "Title": "Example",
        "URL": "https://example.com/login",
        "Username": "user",
        "Password": "secret",
        "Notes": "apple note",
        "OTPAuth": "otpauth://totp/Example?secret=ABC",
    }

    item = plugin.import_row(row)
    assert item.source == "apple_passwords"
    assert item.title == "Example"
    assert item.username == "user"
    assert item.password == "secret"
    assert item.primary_url == "https://example.com/login"
    assert item.notes == "apple note"
    assert item.totp_uri == "otpauth://totp/Example?secret=ABC"

    exported = plugin.export_row(item)
    assert exported["Title"] == "Example"
    assert exported["URL"] == "https://example.com/login"
    assert exported["Username"] == "user"
    assert exported["Password"] == "secret"
    assert exported["Notes"] == "apple note"
    assert exported["OTPAuth"] == "otpauth://totp/Example?secret=ABC"


def test_kaspersky_plugin_basic_mapping() -> None:
    register_kaspersky_plugin()
    registry = get_registry()
    plugin = registry.get(ProviderFormat.KASPERSKY)
    assert isinstance(plugin, KasperskyPlugin)

    row: Dict[str, str] = {
        "Account": "Example",
        "Login": "user",
        "Password": "secret",
        "Url": "https://example.com/login",
    }

    item = plugin.import_row(row)
    assert item.source == "kaspersky"
    assert item.title == "Example"
    assert item.username == "user"
    assert item.password == "secret"
    assert item.primary_url == "https://example.com/login"

    exported = plugin.export_row(item)
    assert exported["Account"] == "Example"
    assert exported["Login"] == "user"
    assert exported["Password"] == "secret"
    assert exported["Url"] == "https://example.com/login"


def test_firefox_plugin_basic_mapping() -> None:
    register_firefox_plugin()
    registry = get_registry()
    plugin = registry.get(ProviderFormat.FIREFOX)
    assert isinstance(plugin, FirefoxPlugin)

    row: Dict[str, str] = {
        "url": "https://example.com/login",
        "username": "user",
        "password": "secret",
        "httpRealm": "",
        "formActionOrigin": "https://example.com/login",
        "guid": "abcd-1234",
        "timeCreated": "1000",
        "timeLastUsed": "2000",
        "timePasswordChanged": "3000",
    }

    item = plugin.import_row(row)
    assert item.source == "firefox"
    assert item.item_type is ItemType.LOGIN
    assert item.source_id == "abcd-1234"
    assert item.username == "user"
    assert item.password == "secret"
    assert item.primary_url == "https://example.com/login"
    assert item.created_at == 1000
    assert item.updated_at == 3000
    assert item.extra.get("formActionOrigin") == "https://example.com/login"

    exported = plugin.export_row(item)
    assert exported["url"] == "https://example.com/login"
    assert exported["username"] == "user"
    assert exported["password"] == "secret"
    assert exported["guid"] == "abcd-1234"
    assert exported["timeCreated"] == "1000"
    assert exported["timePasswordChanged"] == "3000"


def test_chromium_browser_plugin_basic_mapping() -> None:
    register_chromium_browser_plugin()
    registry = get_registry()
    plugin = registry.get(ProviderFormat.CHROMIUM_BROWSER)
    assert isinstance(plugin, ChromiumBrowserPlugin)

    row: Dict[str, str] = {
        "name": "Example",
        "url": "https://example.com/login",
        "username": "user",
        "password": "secret",
        "note": "browser note",
    }

    item = plugin.import_row(row)
    assert item.source == "chromium_browser"
    assert item.title == "Example"
    assert item.username == "user"
    assert item.password == "secret"
    assert item.primary_url == "https://example.com/login"
    assert item.notes == "browser note"

    exported = plugin.export_row(item)
    assert exported["name"] == "Example"
    assert exported["url"] == "https://example.com/login"
    assert exported["username"] == "user"
    assert exported["password"] == "secret"
    assert exported["note"] == "browser note"


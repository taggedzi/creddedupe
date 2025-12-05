# SPDX-License-Identifier: MIT

from __future__ import annotations

from enum import Enum


class ProviderFormat(str, Enum):
    PROTONPASS = "protonpass"
    LASTPASS = "lastpass"
    BITWARDEN = "bitwarden"
    DASHLANE = "dashlane"
    ROBOFORM = "roboform"
    NORDPASS = "nordpass"
    APPLE_PASSWORDS = "apple_passwords"  # Apple Passwords / Safari
    KASPERSKY = "kaspersky"
    FIREFOX = "firefox"
    CHROMIUM_BROWSER = "chromium_browser"  # Chrome, Edge, Brave, Opera
    UNKNOWN = "unknown"


__all__ = ["ProviderFormat"]


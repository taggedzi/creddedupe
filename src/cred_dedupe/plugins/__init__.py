"""Plugin system for provider-specific CSV formats."""

from __future__ import annotations

from .provider_types import ProviderFormat
from .base import BaseProviderPlugin, HeaderSpec
from .registry import ProviderRegistry, get_registry


def register_all_plugins() -> None:
    """Register all built-in provider plugins in the global registry."""
    from .protonpass_plugin import register_protonpass_plugin
    from .lastpass_plugin import register_lastpass_plugin
    from .bitwarden_plugin import register_bitwarden_plugin
    from .dashlane_plugin import register_dashlane_plugin
    from .roboform_plugin import register_roboform_plugin
    from .nordpass_plugin import register_nordpass_plugin
    from .apple_passwords_plugin import register_apple_passwords_plugin
    from .kaspersky_plugin import register_kaspersky_plugin
    from .firefox_plugin import register_firefox_plugin
    from .chromium_browser_plugin import register_chromium_browser_plugin

    register_protonpass_plugin()
    register_lastpass_plugin()
    register_bitwarden_plugin()
    register_dashlane_plugin()
    register_roboform_plugin()
    register_nordpass_plugin()
    register_apple_passwords_plugin()
    register_kaspersky_plugin()
    register_firefox_plugin()
    register_chromium_browser_plugin()


__all__ = [
    "ProviderFormat",
    "BaseProviderPlugin",
    "HeaderSpec",
    "ProviderRegistry",
    "get_registry",
    "register_all_plugins",
]

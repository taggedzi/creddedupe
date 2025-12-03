from __future__ import annotations

from typing import Dict, List

from .base import BaseProviderPlugin
from .provider_types import ProviderFormat


class ProviderRegistry:
    """Registry for provider plugins keyed by :class:`ProviderFormat`."""

    def __init__(self) -> None:
        self._plugins: Dict[ProviderFormat, BaseProviderPlugin] = {}

    def register(self, plugin: BaseProviderPlugin) -> None:
        """Register a plugin instance for its declared provider type.

        Raises:
            ValueError: if a plugin for the provider type is already registered.
        """
        provider_type = plugin.provider_type
        if provider_type in self._plugins:
            raise ValueError(f"Provider plugin already registered: {provider_type}")
        self._plugins[provider_type] = plugin

    def get(self, provider_type: ProviderFormat) -> BaseProviderPlugin:
        """Return the plugin registered for ``provider_type``."""
        try:
            return self._plugins[provider_type]
        except KeyError as exc:  # pragma: no cover - simple error path
            raise KeyError(f"No plugin registered for provider: {provider_type!r}") from exc

    def all_plugins(self) -> List[BaseProviderPlugin]:
        """Return a list of all registered plugins."""
        return list(self._plugins.values())


_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """Return the global provider registry singleton."""
    return _registry


__all__ = ["ProviderRegistry", "get_registry"]


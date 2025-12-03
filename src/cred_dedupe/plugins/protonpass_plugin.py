from __future__ import annotations

from typing import Dict

from ..core import CSV_INPUT_COLUMNS
from ..model import VaultItem
from ..protonpass import proton_row_to_vault_item, vault_item_to_proton_row
from .base import BaseProviderPlugin, HeaderSpec
from .provider_types import ProviderFormat
from .registry import get_registry


class ProtonPassPlugin(BaseProviderPlugin):
    """Provider plugin for Proton Pass CSV format."""

    provider_type = ProviderFormat.PROTONPASS
    header_spec = HeaderSpec(
        required=set(CSV_INPUT_COLUMNS),
        optional=set(),
    )

    def import_row(self, row: Dict[str, str]) -> VaultItem:
        return proton_row_to_vault_item(row)

    def export_row(self, item: VaultItem) -> Dict[str, str]:
        return vault_item_to_proton_row(item)


def register_protonpass_plugin() -> None:
    """Register the Proton Pass plugin in the global registry.

    Safe to call multiple times; subsequent calls are ignored once registered.
    """
    registry = get_registry()
    try:
        registry.register(ProtonPassPlugin())
    except ValueError:
        # Already registered; nothing to do.
        pass


__all__ = ["ProtonPassPlugin", "register_protonpass_plugin"]


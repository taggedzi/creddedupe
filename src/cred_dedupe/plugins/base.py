from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Set

from ..model import VaultItem
from .provider_types import ProviderFormat


@dataclass(frozen=True)
class HeaderSpec:
    """Simple structure to describe provider header expectations."""

    required: Set[str]
    optional: Set[str]


class BaseProviderPlugin(ABC):
    """Base class for all provider plugins.

    Each plugin knows how to map provider-specific CSV rows to and from the
    canonical :class:`VaultItem` model.
    """

    provider_type: ProviderFormat
    header_spec: HeaderSpec

    def __init__(self) -> None:
        if not hasattr(self, "provider_type"):
            raise ValueError("Provider plugin must define provider_type")
        if not hasattr(self, "header_spec"):
            raise ValueError("Provider plugin must define header_spec")

    @abstractmethod
    def import_row(self, row: Dict[str, str]) -> VaultItem:
        """Convert a provider-specific CSV row dict into a :class:`VaultItem`."""
        raise NotImplementedError

    @abstractmethod
    def export_row(self, item: VaultItem) -> Dict[str, str]:
        """Convert a :class:`VaultItem` into a provider-specific CSV row dict."""
        raise NotImplementedError

    def normalize_header(self, header: str) -> str:
        """Normalize a header name for internal comparison.

        Default behavior: lowercase and strip surrounding whitespace.
        Providers can override this if they need more complex logic.
        """
        return header.strip().lower()

    def normalized_required_headers(self) -> Set[str]:
        return {self.normalize_header(h) for h in self.header_spec.required}

    def normalized_optional_headers(self) -> Set[str]:
        return {self.normalize_header(h) for h in self.header_spec.optional}


__all__ = ["HeaderSpec", "BaseProviderPlugin"]


# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Dict

from cred_dedupe.core import CSV_INPUT_COLUMNS
from cred_dedupe.detection import (
    DetectionResult,
    detect_provider,
)
from cred_dedupe.plugins.base import BaseProviderPlugin, HeaderSpec
from cred_dedupe.plugins.provider_types import ProviderFormat
from cred_dedupe.plugins.registry import get_registry
from cred_dedupe.plugins.protonpass_plugin import register_protonpass_plugin


def test_detect_provider_no_headers_returns_unknown() -> None:
    registry = get_registry()
    result = detect_provider([], registry)

    assert isinstance(result, DetectionResult)
    assert result.provider is ProviderFormat.UNKNOWN
    assert result.confidence == 0.0
    assert result.matches == []


def test_detect_provider_proton_headers() -> None:
    register_protonpass_plugin()
    registry = get_registry()

    headers = list(CSV_INPUT_COLUMNS)
    result = detect_provider(headers, registry)

    assert result.provider is ProviderFormat.PROTONPASS
    assert result.confidence >= 0.8
    assert any(m.provider is ProviderFormat.PROTONPASS for m in result.matches)


def test_detect_provider_unknown_headers() -> None:
    register_protonpass_plugin()
    registry = get_registry()

    headers = ["foo", "bar", "baz"]
    result = detect_provider(headers, registry)

    assert result.provider is ProviderFormat.UNKNOWN
    assert result.confidence == 0.0
    assert result.matches == []


class _DummyLastPassPlugin(BaseProviderPlugin):
    provider_type = ProviderFormat.LASTPASS
    header_spec = HeaderSpec(
        required={"dummy name", "dummy_url"},
        optional={"dummy_extra"},
    )

    def import_row(self, row: Dict[str, str]):
        raise NotImplementedError

    def export_row(self, item):
        raise NotImplementedError


def test_detection_prefers_higher_scoring_plugin_when_multiple() -> None:
    registry = get_registry()
    # Preserve existing registry state so this test does not interfere with
    # other plugin registration tests.
    original_plugins = dict(registry._plugins)  # type: ignore[attr-defined]
    try:
        registry._plugins.clear()  # type: ignore[attr-defined]
        register_protonpass_plugin()

        # Register a dummy plugin with headers that will match our test CSV
        # better than the ProtonPass plugin.
        registry.register(_DummyLastPassPlugin())

        headers = ["Dummy Name", "dummy_url", "DUMMY_EXTRA"]
        result = detect_provider(headers, registry)

        assert result.provider is ProviderFormat.LASTPASS
        assert any(m.provider is ProviderFormat.LASTPASS for m in result.matches)
    finally:
        registry._plugins = original_plugins  # type: ignore[attr-defined]


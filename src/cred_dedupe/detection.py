from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .plugins.base import BaseProviderPlugin
from .plugins.provider_types import ProviderFormat
from .plugins.registry import ProviderRegistry


@dataclass
class DetectionMatchDetails:
    provider: ProviderFormat
    score: float
    matched_required: int
    total_required: int
    matched_optional: int
    total_optional: int


@dataclass
class DetectionResult:
    provider: ProviderFormat
    confidence: float
    matches: List[DetectionMatchDetails]
    reason: str


def normalize_header_value(header: str) -> str:
    """
    Normalize a CSV header for detection.

    - Strip leading/trailing whitespace.
    - Lowercase.
    - Remove surrounding quotes.
    - Strip a trailing ':' if present.
    """
    h = header.strip().strip('"').strip("'")
    h = h.lower()
    if h.endswith(":"):
        h = h[:-1]
    return h


def score_headers_for_plugin(
    headers: Iterable[str],
    plugin: BaseProviderPlugin,
) -> DetectionMatchDetails:
    normalized_headers = {normalize_header_value(h) for h in headers}

    required = plugin.normalized_required_headers()
    optional = plugin.normalized_optional_headers()

    matched_required = len(required & normalized_headers)
    matched_optional = len(optional & normalized_headers)
    total_required = len(required)
    total_optional = len(optional)

    required_ratio = matched_required / total_required if total_required else 0.0
    optional_ratio = matched_optional / total_optional if total_optional else 0.0

    score = required_ratio + 0.25 * optional_ratio

    return DetectionMatchDetails(
        provider=plugin.provider_type,
        score=score,
        matched_required=matched_required,
        total_required=total_required,
        matched_optional=matched_optional,
        total_optional=total_optional,
    )


def detect_provider(headers: List[str], registry: ProviderRegistry) -> DetectionResult:
    """
    Inspect the header row of a CSV and attempt to detect which provider format it matches.
    """
    if not headers:
        return DetectionResult(
            provider=ProviderFormat.UNKNOWN,
            confidence=0.0,
            matches=[],
            reason="No headers provided",
        )

    plugins = registry.all_plugins()
    if not plugins:
        return DetectionResult(
            provider=ProviderFormat.UNKNOWN,
            confidence=0.0,
            matches=[],
            reason="No provider plugins registered",
        )

    matches = [score_headers_for_plugin(headers, plugin) for plugin in plugins]
    matches = [m for m in matches if m.score > 0.0]
    if not matches:
        return DetectionResult(
            provider=ProviderFormat.UNKNOWN,
            confidence=0.0,
            matches=[],
            reason="No plugin matched the header row",
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    best = matches[0]

    confidence = max(0.0, min(1.0, best.score))
    provider = best.provider

    reason = (
        f"Best match: {provider.value} "
        f"(score={best.score:.2f}, "
        f"matched_required={best.matched_required}/{best.total_required}, "
        f"matched_optional={best.matched_optional}/{best.total_optional})."
    )

    return DetectionResult(
        provider=provider,
        confidence=confidence,
        matches=matches,
        reason=reason,
    )


def detect_provider_for_file(
    path,
    registry: ProviderRegistry,
) -> DetectionResult:
    """
    Convenience helper for backends/GUI to detect a provider given a CSV file path.
    """
    import csv
    from pathlib import Path

    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return DetectionResult(
                provider=ProviderFormat.UNKNOWN,
                confidence=0.0,
                matches=[],
                reason="CSV file is empty",
            )

    return detect_provider(list(headers), registry)


__all__ = [
    "DetectionMatchDetails",
    "DetectionResult",
    "normalize_header_value",
    "score_headers_for_plugin",
    "detect_provider",
    "detect_provider_for_file",
]

